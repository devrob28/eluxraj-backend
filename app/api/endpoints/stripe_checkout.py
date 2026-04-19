from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import stripe
import os
import secrets
from app.db.session import get_db
from app.models.user import User
from app.core.security import get_password_hash
from app.core.logging import logger
from app.services.email import email_service

router = APIRouter()

# Stripe configuration from environment variables ONLY
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class CheckoutRequest(BaseModel):
    success_url: str = "https://eluxraj.ai/welcome.html?session_id={CHECKOUT_SESSION_ID}"
    cancel_url: str = "https://eluxraj.ai/"

@router.post("/create-checkout-session")
async def create_checkout_session(req: CheckoutRequest):
    """Create a Stripe Checkout session for $98/month subscription"""
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    try:
        # Get or create price
        price_id = os.getenv("STRIPE_PRICE_ID")
        
        if not price_id:
            # Create product and price on the fly
            products = stripe.Product.list(limit=10)
            existing = next((p for p in products.data if p.name == "ELUXRAJ Pro Membership"), None)
            
            if existing:
                product_id = existing.id
            else:
                product = stripe.Product.create(
                    name="ELUXRAJ Pro Membership",
                    description="AI-powered trading signals • 78% win rate • Chart AI • Real-time alerts • Elite community"
                )
                product_id = product.id
            
            # Check for existing price
            prices = stripe.Price.list(product=product_id, active=True)
            existing_price = next((p for p in prices.data if p.unit_amount == 9800 and p.recurring), None)
            
            if existing_price:
                price_id = existing_price.id
            else:
                price = stripe.Price.create(
                    product=product_id,
                    unit_amount=9800,  # $98.00
                    currency="usd",
                    recurring={"interval": "month"}
                )
                price_id = price.id
        
        # Create checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1
            }],
            mode="subscription",
            success_url=req.success_url,
            cancel_url=req.cancel_url,
            allow_promotion_codes=True,
            billing_address_collection="required",
            metadata={
                "product": "eluxraj_pro"
            }
        )
        
        return {
            "checkout_url": session.url,
            "session_id": session.id
        }
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/verify-session/{session_id}")
async def verify_session(session_id: str):
    """Verify a checkout session and get customer info"""
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status == "paid":
            return {
                "paid": True,
                "customer_email": session.customer_details.email if session.customer_details else None,
                "customer_name": session.customer_details.name if session.customer_details else None,
                "subscription_id": session.subscription,
                "customer_id": session.customer
            }
        else:
            return {
                "paid": False,
                "status": session.payment_status
            }
            
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle Stripe webhooks for subscription lifecycle:
    - checkout.session.completed → create/upgrade user to Pro, email password setup link
    - customer.subscription.deleted → downgrade user to lite
    - invoice.payment_failed → log for monitoring
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    # Signature verification — REQUIRED in production
    try:
        if webhook_secret:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        else:
            # Dev fallback only — never trust unsigned webhooks in prod
            logger.warning("⚠️ STRIPE_WEBHOOK_SECRET not set — accepting unsigned webhook (dev only)")
            import json
            event = json.loads(payload)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"❌ Stripe webhook signature invalid: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"❌ Stripe webhook parse error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    event_type = event.get("type", "")
    event_id = event.get("id", "unknown")
    logger.info(f"📬 Stripe webhook received: {event_type} ({event_id})")

    try:
        if event_type == "checkout.session.completed":
            await _handle_checkout_completed(event["data"]["object"], db)

        elif event_type == "customer.subscription.deleted":
            await _handle_subscription_deleted(event["data"]["object"], db)

        elif event_type == "invoice.payment_failed":
            await _handle_payment_failed(event["data"]["object"], db)

        else:
            # Acknowledge unknown events so Stripe stops retrying
            logger.info(f"↪️  Ignoring event type: {event_type}")

    except Exception as e:
        logger.error(f"❌ Webhook handler failed for {event_type}: {e}", exc_info=True)
        # Return 200 anyway — we don't want Stripe to retry and cause duplicate charges
        # The error is logged; we can reconcile manually

    return {"status": "success"}


async def _handle_checkout_completed(session: dict, db: Session):
    """Create new user OR upgrade existing user to Pro, then email them a password setup link."""
    # Extract customer info from the Stripe session
    customer_details = session.get("customer_details") or {}
    email = (customer_details.get("email") or session.get("customer_email") or "").lower().strip()
    full_name = customer_details.get("name") or ""
    stripe_customer_id = session.get("customer")
    stripe_subscription_id = session.get("subscription")

    if not email:
        logger.error(f"❌ checkout.session.completed missing email — session={session.get('id')}")
        return

    logger.info(f"💳 Processing paid checkout for {email}")

    # Idempotency: if this subscription_id is already attached to a user, skip entirely
    if stripe_subscription_id:
        existing = db.query(User).filter(User.stripe_subscription_id == stripe_subscription_id).first()
        if existing:
            logger.info(f"↪️  Subscription {stripe_subscription_id} already linked to user {existing.id}, skipping")
            return

    # Look up existing user by email
    user = db.query(User).filter(User.email == email).first()
    is_new_user = user is None

    if is_new_user:
        # Create a new user with a random password (they'll set their own via reset link)
        random_password = secrets.token_urlsafe(32)
        reset_token = secrets.token_urlsafe(32)

        user = User(
            email=email,
            hashed_password=get_password_hash(random_password),
            full_name=full_name or None,
            subscription_tier="pro",
            stripe_customer_id=stripe_customer_id,
            stripe_subscription_id=stripe_subscription_id,
            is_active=True,
            is_verified=True,
            email_alerts=True,
            push_alerts=True,
            reset_token=reset_token,
            reset_token_expires=datetime.utcnow() + timedelta(hours=24),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"✨ Created new Pro user {user.id} ({email})")
    else:
        # Existing user — upgrade to Pro and issue a fresh reset token so they can set/change password
        reset_token = secrets.token_urlsafe(32)
        user.subscription_tier = "pro"
        user.stripe_customer_id = stripe_customer_id
        user.stripe_subscription_id = stripe_subscription_id
        user.is_active = True
        user.reset_token = reset_token
        user.reset_token_expires = datetime.utcnow() + timedelta(hours=24)
        if full_name and not user.full_name:
            user.full_name = full_name
        db.commit()
        logger.info(f"⬆️  Upgraded existing user {user.id} ({email}) to Pro")

    # Send welcome email with password setup link
    reset_url = f"https://eluxraj.ai/reset-password.html?token={reset_token}"
    try:
        sent = await email_service.send_pro_welcome_email(
            to_email=email,
            reset_url=reset_url,
            full_name=user.full_name,
        )
        if sent:
            logger.info(f"📧 Welcome email sent to {email}")
        else:
            logger.warning(f"⚠️  Welcome email failed to send to {email} (reset token still valid)")
    except Exception as e:
        logger.error(f"❌ Welcome email exception for {email}: {e}")


async def _handle_subscription_deleted(subscription: dict, db: Session):
    """Downgrade user to lite when their subscription is cancelled."""
    sub_id = subscription.get("id")
    customer_id = subscription.get("customer")

    if not sub_id:
        logger.error("❌ subscription.deleted missing id")
        return

    # Find user by subscription_id first, fall back to customer_id
    user = db.query(User).filter(User.stripe_subscription_id == sub_id).first()
    if not user and customer_id:
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()

    if not user:
        logger.warning(f"⚠️  No user found for cancelled subscription {sub_id}")
        return

    user.subscription_tier = "lite"
    user.stripe_subscription_id = None
    db.commit()
    logger.info(f"⬇️  Downgraded user {user.id} ({user.email}) to lite after cancellation")


async def _handle_payment_failed(invoice: dict, db: Session):
    """Log failed payment — Stripe will auto-retry and eventually cancel if it keeps failing."""
    customer_id = invoice.get("customer")
    amount = invoice.get("amount_due", 0) / 100
    attempt = invoice.get("attempt_count", 1)

    user = None
    if customer_id:
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()

    if user:
        logger.warning(f"💸 Payment failed for {user.email} — ${amount} (attempt {attempt})")
    else:
        logger.warning(f"💸 Payment failed for unknown customer {customer_id} — ${amount}")
