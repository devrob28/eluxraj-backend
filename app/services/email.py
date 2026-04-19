import os
from typing import Optional, List, Dict, Any
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, Personalization
from app.core.config import settings
from app.core.logging import logger

class EmailService:
    """Email service using SendGrid"""
    
    def __init__(self):
        self.api_key = settings.SENDGRID_API_KEY
        self.from_email = settings.FROM_EMAIL
        self.client = None
        
        if self.api_key:
            self.client = SendGridAPIClient(self.api_key)
            logger.info("✅ Email service initialized")
        else:
            logger.warning("⚠️ SendGrid API key not set - emails disabled")
    
    def is_enabled(self) -> bool:
        return self.client is not None
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send a single email"""
        if not self.is_enabled():
            logger.warning("Email not sent - service disabled")
            return False
        
        try:
            message = Mail(
                from_email=Email(self.from_email, "ELUXRAJ Signals"),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )
            
            if text_content:
                message.add_content(Content("text/plain", text_content))
            
            response = self.client.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"✅ Email sent to {to_email}")
                return True
            else:
                logger.error(f"❌ Email failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Email error: {e}")
            return False
    
    async def send_signal_alert(
        self,
        to_email: str,
        user_name: str,
        signal: Dict[str, Any]
    ) -> bool:
        """Send a trading signal alert email"""
        
        # Determine signal color
        if signal["signal_type"] == "buy":
            signal_color = "#22c55e"  # Green
            signal_emoji = "🟢"
            action = "BUY"
        elif signal["signal_type"] == "sell":
            signal_color = "#ef4444"  # Red
            signal_emoji = "🔴"
            action = "SELL"
        else:
            signal_color = "#f59e0b"  # Yellow
            signal_emoji = "🟡"
            action = "HOLD"
        
        subject = f"{signal_emoji} {action} Signal: {signal['symbol']} (Score: {signal['oracle_score']})"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin:0;padding:0;background:#0a0a0f;font-family:Arial,sans-serif;">
            <div style="max-width:600px;margin:0 auto;padding:20px;">
                <!-- Header -->
                <div style="text-align:center;padding:30px 0;border-bottom:1px solid #333;">
                    <h1 style="margin:0;color:#fff;font-size:28px;">
                        <span style="background:linear-gradient(135deg,#7c3aed,#06b6d4);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">ELUXRAJ</span>
                    </h1>
                    <p style="color:#888;margin:10px 0 0;">AI-Powered Trading Signals</p>
                </div>
                
                <!-- Signal Card -->
                <div style="background:#12121a;border:1px solid #333;border-radius:16px;padding:30px;margin:30px 0;">
                    <div style="text-align:center;margin-bottom:20px;">
                        <span style="background:{signal_color};color:#fff;padding:8px 24px;border-radius:20px;font-weight:bold;font-size:18px;">
                            {signal_emoji} {action} {signal['symbol']}
                        </span>
                    </div>
                    
                    <!-- Oracle Score -->
                    <div style="text-align:center;padding:20px 0;border-bottom:1px solid #333;">
                        <p style="color:#888;margin:0;font-size:12px;text-transform:uppercase;">Oracle Score</p>
                        <p style="color:#fff;margin:10px 0 0;font-size:48px;font-weight:bold;">
                            <span style="background:linear-gradient(135deg,#7c3aed,#06b6d4);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">{signal['oracle_score']}</span>
                        </p>
                    </div>
                    
                    <!-- Price Targets -->
                    <div style="display:flex;justify-content:space-between;padding:20px 0;border-bottom:1px solid #333;">
                        <div style="text-align:center;flex:1;">
                            <p style="color:#888;margin:0;font-size:12px;">ENTRY</p>
                            <p style="color:#fff;margin:5px 0 0;font-size:18px;font-weight:bold;">${signal['entry_price']:,.2f}</p>
                        </div>
                        <div style="text-align:center;flex:1;">
                            <p style="color:#888;margin:0;font-size:12px;">TARGET</p>
                            <p style="color:#22c55e;margin:5px 0 0;font-size:18px;font-weight:bold;">${signal['target_price']:,.2f}</p>
                        </div>
                        <div style="text-align:center;flex:1;">
                            <p style="color:#888;margin:0;font-size:12px;">STOP LOSS</p>
                            <p style="color:#ef4444;margin:5px 0 0;font-size:18px;font-weight:bold;">${signal['stop_loss']:,.2f}</p>
                        </div>
                    </div>
                    
                    <!-- AI Reasoning -->
                    <div style="padding:20px 0;">
                        <p style="color:#888;margin:0 0 10px;font-size:12px;text-transform:uppercase;">🧠 AI Reasoning</p>
                        <p style="color:#fff;margin:0;font-size:14px;line-height:1.6;background:#1a1a2e;padding:15px;border-radius:8px;">
                            {signal['reasoning_summary']}
                        </p>
                    </div>
                    
                    <!-- Meta Info -->
                    <div style="display:flex;justify-content:space-between;padding-top:20px;border-top:1px solid #333;">
                        <div>
                            <p style="color:#888;margin:0;font-size:11px;">Risk/Reward</p>
                            <p style="color:#fff;margin:3px 0 0;font-size:14px;font-weight:bold;">{signal['risk_reward_ratio']}:1</p>
                        </div>
                        <div>
                            <p style="color:#888;margin:0;font-size:11px;">Timeframe</p>
                            <p style="color:#fff;margin:3px 0 0;font-size:14px;font-weight:bold;">{signal['timeframe']}</p>
                        </div>
                        <div>
                            <p style="color:#888;margin:0;font-size:11px;">Pair</p>
                            <p style="color:#fff;margin:3px 0 0;font-size:14px;font-weight:bold;">{signal['pair']}</p>
                        </div>
                    </div>
                </div>
                
                <!-- CTA Button -->
                <div style="text-align:center;margin:30px 0;">
                    <a href="https://eluxraj.ai/signals" style="background:linear-gradient(135deg,#7c3aed,#06b6d4);color:#fff;padding:16px 40px;border-radius:12px;text-decoration:none;font-weight:bold;display:inline-block;">
                        View All Signals →
                    </a>
                </div>
                
                <!-- Disclaimer -->
                <div style="text-align:center;padding:20px 0;border-top:1px solid #333;">
                    <p style="color:#666;font-size:11px;margin:0;">
                        ⚠️ This is not financial advice. Trading involves risk. Past performance does not guarantee future results.
                    </p>
                </div>
                
                <!-- Footer -->
                <div style="text-align:center;padding:20px 0;">
                    <p style="color:#666;font-size:12px;margin:0;">
                        ELUXRAJ™ | AI-Powered Trading Signals
                    </p>
                    <p style="color:#444;font-size:11px;margin:10px 0 0;">
                        <a href="https://eluxraj.ai/unsubscribe" style="color:#444;">Unsubscribe</a> · 
                        <a href="https://eluxraj.ai/preferences" style="color:#444;">Preferences</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
ELUXRAJ Signal Alert

{action} {signal['symbol']} - Oracle Score: {signal['oracle_score']}

Entry: ${signal['entry_price']:,.2f}
Target: ${signal['target_price']:,.2f}
Stop Loss: ${signal['stop_loss']:,.2f}
Risk/Reward: {signal['risk_reward_ratio']}:1
Timeframe: {signal['timeframe']}

AI Reasoning:
{signal['reasoning_summary']}

---
This is not financial advice. Trading involves risk.
ELUXRAJ - AI-Powered Trading Signals
        """
        
        return await self.send_email(to_email, subject, html_content, text_content)
    
    async def send_welcome_email(self, to_email: str, user_name: str) -> bool:
        """Send welcome email to new users"""
        
        subject = "🚀 Welcome to ELUXRAJ - Your AI Trading Signals Await!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
        </head>
        <body style="margin:0;padding:0;background:#0a0a0f;font-family:Arial,sans-serif;">
            <div style="max-width:600px;margin:0 auto;padding:20px;">
                <div style="text-align:center;padding:40px 0;">
                    <h1 style="color:#fff;margin:0 0 20px;">Welcome to <span style="background:linear-gradient(135deg,#7c3aed,#06b6d4);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">ELUXRAJ</span></h1>
                    <p style="color:#888;font-size:18px;margin:0;">Hey {user_name or 'Trader'}! 👋</p>
                </div>
                
                <div style="background:#12121a;border-radius:16px;padding:30px;margin:20px 0;">
                    <h2 style="color:#fff;margin:0 0 20px;">Your AI-powered trading journey starts now!</h2>
                    <p style="color:#aaa;line-height:1.7;">
                        You now have access to the same AI intelligence used by professional traders. Here's what you can do:
                    </p>
                    <ul style="color:#aaa;line-height:2;">
                        <li>📊 Get real-time trading signals</li>
                        <li>🧠 Understand the AI reasoning behind each signal</li>
                        <li>🐳 Track whale movements</li>
                        <li>📈 Monitor market sentiment</li>
                    </ul>
                </div>
                
                <div style="text-align:center;margin:30px 0;">
                    <a href="https://eluxraj.ai/dashboard" style="background:linear-gradient(135deg,#7c3aed,#06b6d4);color:#fff;padding:16px 40px;border-radius:12px;text-decoration:none;font-weight:bold;display:inline-block;">
                        View Your Dashboard →
                    </a>
                </div>
                
                <div style="text-align:center;padding:20px 0;border-top:1px solid #333;">
                    <p style="color:#666;font-size:12px;">Questions? Reply to this email or contact support@eluxraj.ai</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(to_email, subject, html_content)


    async def send_pro_welcome_email(
        self,
        to_email: str,
        reset_url: str,
        full_name: Optional[str] = None
    ) -> bool:
        """Send welcome email to new paying Pro members with password setup link."""
        
        subject = "🔥 Welcome to ELUXRAJ Pro — Set Your Password"
        greeting = full_name.split()[0] if full_name else "Trader"
        
        html_content = """
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#0a0a0f;font-family:Arial,sans-serif;">
    <div style="max-width:600px;margin:0 auto;padding:20px;">
        <div style="text-align:center;padding:40px 0;">
            <h1 style="color:#fff;margin:0 0 20px;">Welcome to <span style="background:linear-gradient(135deg,#7c3aed,#06b6d4);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">ELUXRAJ PRO</span></h1>
            <p style="color:#22c55e;font-size:18px;margin:0;font-weight:bold;">✓ Payment confirmed — GREETING_PLACEHOLDER!</p>
        </div>
        <div style="background:#12121a;border:1px solid #22c55e;border-radius:16px;padding:30px;margin:20px 0;">
            <h2 style="color:#fff;margin:0 0 16px;">One last step: set your password</h2>
            <p style="color:#aaa;line-height:1.7;margin:0 0 24px;">Your Pro account is ready. Click below to set your password and start using your AI Trading Playbooks, Chart AI, and Live Signals immediately.</p>
            <div style="text-align:center;margin:30px 0;">
                <a href="RESET_URL_PLACEHOLDER" style="background:linear-gradient(135deg,#7c3aed,#06b6d4);color:#fff;padding:18px 48px;border-radius:12px;text-decoration:none;font-weight:bold;display:inline-block;font-size:16px;">Set My Password →</a>
            </div>
            <p style="color:#666;font-size:12px;text-align:center;margin:20px 0 0;">This link expires in 24 hours. If it expires, visit <a href="https://eluxraj.ai/forgot-password.html" style="color:#06b6d4;">forgot-password.html</a> to request a new one.</p>
        </div>
        <div style="background:#12121a;border-radius:16px;padding:24px;margin:20px 0;">
            <h3 style="color:#fff;margin:0 0 12px;font-size:16px;">What\'s unlocked for you:</h3>
            <ul style="color:#aaa;line-height:2;margin:0;padding-left:20px;">
                <li>📋 AI Trading Playbooks — complete setups</li>
                <li>📊 Chart AI — upload any chart, get instant analysis</li>
                <li>🎯 Live Signals — 50 stocks, scanned every 15 min</li>
                <li>🔔 Real-time push notifications</li>
                <li>💬 Elite community access</li>
            </ul>
        </div>
        <div style="text-align:center;padding:20px 0;border-top:1px solid #333;">
            <p style="color:#666;font-size:12px;">Questions? Reply to this email.</p>
            <p style="color:#444;font-size:11px;margin:10px 0 0;">ELUXRAJ™ · $98/mo · Cancel anytime from your dashboard</p>
        </div>
    </div>
</body>
</html>
""".replace("GREETING_PLACEHOLDER", greeting).replace("RESET_URL_PLACEHOLDER", reset_url)
        
        text_content = f"""Welcome to ELUXRAJ Pro!

Your payment is confirmed. Set your password to activate your account:

{reset_url}

This link expires in 24 hours.

Once logged in, you'll have full access to:
- AI Trading Playbooks
- Chart AI analysis
- Live Signals (50 stocks)
- Real-time alerts
- Elite community

Questions? Reply to this email.

ELUXRAJ - $98/mo - Cancel anytime
"""
        
        return await self.send_email(to_email, subject, html_content, text_content)


# Initialize email service
email_service = EmailService()
