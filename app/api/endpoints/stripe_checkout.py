from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import stripe
import os

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
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    
    try:
        if webhook_secret:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        else:
            import json
            event = json.loads(payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    event_type = event.get("type", "")
    
    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        print(f"✅ Payment successful: {session.get('customer_email', 'unknown')}")
        
    elif event_type == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        print(f"❌ Subscription cancelled: {subscription['id']}")
    
    return {"status": "success"}
