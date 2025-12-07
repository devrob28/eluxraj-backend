from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.db.session import get_db
from app.models.signal import Signal
from app.models.user import User

router = APIRouter()

@router.get("/homepage")
async def get_homepage_copy(db: Session = Depends(get_db)):
    """Get compliant homepage marketing copy"""
    
    # Get real stats for social proof
    total_signals = db.query(Signal).count()
    total_users = db.query(User).count()
    
    completed = db.query(Signal).filter(
        Signal.status.in_(["hit_target", "hit_stop", "expired"])
    ).all()
    wins = [s for s in completed if s.status == "hit_target"]
    win_rate = round(len(wins) / len(completed) * 100, 1) if completed else 0
    
    first = db.query(Signal).order_by(Signal.created_at.asc()).first()
    days_live = (datetime.utcnow() - first.created_at).days if first and first.created_at else 0
    
    return {
        "hero": {
            "headline": "AI Trade Signals That Identify Profit Opportunities Before Most Traders Do",
            "subheadline": "Know what to buy, when to enter, and why — powered by institutional-style models, delivered in real time. No hype. Just data, logic, and risk clearly explained.",
            "cta_primary": "Start Free",
            "cta_secondary": "See Live Results",
            "cta_secondary_link": "/track"
        },
        
        "disclaimer_banner": {
            "text": "⚠️ Not financial advice. Trading involves substantial risk. Past performance does not guarantee future results. Only trade what you can afford to lose.",
            "placement": "Directly under hero headline"
        },
        
        "value_props": [
            {
                "icon": "🎯",
                "title": "Clear Entry & Exit Points",
                "description": "Every signal includes specific entry price, profit target, and stop-loss. No vague predictions — just actionable levels."
            },
            {
                "icon": "🧠",
                "title": "AI-Explained Reasoning",
                "description": "Understand exactly why each signal was generated. Our ORACLE engine shows the data factors behind every decision."
            },
            {
                "icon": "⚖️",
                "title": "Risk Quantified Upfront",
                "description": "See risk/reward ratio, confidence score, and suggested position sizing before you decide."
            },
            {
                "icon": "⏱️",
                "title": "Real-Time Delivery",
                "description": "Signals delivered instantly via app, email, and push notifications. No delays for premium members."
            }
        ],
        
        "how_it_works": {
            "title": "How ORACLE Generates Signals",
            "subtitle": "Our AI analyzes 7 data factors to score opportunities from 0-100",
            "steps": [
                {
                    "step": 1,
                    "title": "Data Collection",
                    "description": "ORACLE pulls real-time price, volume, sentiment, and market data from public sources."
                },
                {
                    "step": 2,
                    "title": "Factor Analysis",
                    "description": "7 weighted factors are scored: momentum, trend, volume, sentiment, volatility, whale activity, and value."
                },
                {
                    "step": 3,
                    "title": "Signal Generation",
                    "description": "Scores above 65 trigger BUY signals. Below 35 trigger SELL. Each includes entry, target, and stop."
                },
                {
                    "step": 4,
                    "title": "Reasoning Delivered",
                    "description": "You see exactly which factors drove the signal and why — not a black box."
                }
            ],
            "cta": "View Full Methodology",
            "cta_link": "/api/v1/content/how-oracle-works"
        },
        
        "social_proof": {
            "stats": [
                {
                    "value": str(total_signals),
                    "label": "Signals Generated",
                    "footnote": "All logged and auditable"
                },
                {
                    "value": f"{days_live}",
                    "label": "Days Live",
                    "footnote": "Building track record publicly"
                },
                {
                    "value": f"{win_rate}%" if completed else "—",
                    "label": "Historical Win Rate",
                    "footnote": "Past performance ≠ future results"
                },
                {
                    "value": str(total_users),
                    "label": "Traders Joined",
                    "footnote": None
                }
            ],
            "disclaimer": "Statistics reflect historical signal performance during measured period. Not indicative of future results."
        },
        
        "transparency_section": {
            "title": "Radical Transparency",
            "subtitle": "We publish everything. Every signal. Every outcome. Every limitation.",
            "points": [
                "✓ Every signal timestamped and logged publicly",
                "✓ Win rate calculated from ALL signals (not cherry-picked)",
                "✓ Full methodology published — no black boxes",
                "✓ Limitations listed honestly (see 'Why We Might Be Wrong')",
                "✓ Download raw data anytime for independent verification"
            ],
            "cta": "View Public Signal Tracker",
            "cta_link": "/track"
        },
        
        "pricing": {
            "title": "Choose Your Plan",
            "subtitle": "Start free. Upgrade when you see value.",
            "disclaimer": "Subscription provides access to signals and tools. Profitability not guaranteed.",
            "plans": [
                {
                    "name": "Free",
                    "price": "$0",
                    "period": "forever",
                    "description": "Test the waters",
                    "features": [
                        "3 assets (BTC, ETH, SOL)",
                        "2-hour delayed signals",
                        "Basic signal data",
                        "Public signal tracker access"
                    ],
                    "cta": "Start Free",
                    "highlighted": False
                },
                {
                    "name": "Pro",
                    "price": "$49",
                    "period": "/month",
                    "description": "For active traders",
                    "features": [
                        "All 12+ supported assets",
                        "Real-time signals",
                        "Full AI reasoning breakdown",
                        "Email alerts",
                        "Performance analytics"
                    ],
                    "cta": "Go Pro",
                    "highlighted": True,
                    "note": "Most popular"
                },
                {
                    "name": "Elite",
                    "price": "$99",
                    "period": "/month",
                    "description": "For serious traders",
                    "features": [
                        "Everything in Pro",
                        "Priority signal delivery",
                        "Market-wide scanning",
                        "Whale activity alerts",
                        "API access",
                        "Direct support"
                    ],
                    "cta": "Go Elite",
                    "highlighted": False
                }
            ]
        },
        
        "faq": {
            "title": "Frequently Asked Questions",
            "items": [
                {
                    "question": "Is this financial advice?",
                    "answer": "No. ELUXRAJ provides informational signals based on AI analysis of public market data. This is not personalized financial advice. Always do your own research and consult a licensed financial advisor before trading."
                },
                {
                    "question": "What's your win rate?",
                    "answer": f"Our historical win rate (signals hitting target vs total completed) is currently {win_rate}% based on {len(completed)} completed signals. This is a limited sample size and past performance does not guarantee future results. View all signals at /track."
                },
                {
                    "question": "How is ORACLE different from other signal services?",
                    "answer": "Transparency. We publish our exact methodology, every signal is logged publicly, and we openly list our limitations. Most services hide this information. We believe you deserve to know exactly what you're getting."
                },
                {
                    "question": "What data sources do you use?",
                    "answer": "We use publicly available data: CoinGecko for price/volume data, Alternative.me for Fear & Greed Index, and pattern-based whale activity detection (real on-chain integration coming soon). No proprietary order flow or insider data."
                },
                {
                    "question": "Can I lose money following these signals?",
                    "answer": "Yes. Absolutely. Trading is risky and losses are common. Our signals are probabilistic — they're often wrong. Never trade with money you can't afford to lose. We include stop-loss levels with every signal specifically because losses happen."
                },
                {
                    "question": "Why should I pay when there are free signals everywhere?",
                    "answer": "You shouldn't — until we've proven value to you. Start free. Track our public results. Only upgrade if our signals consistently provide useful insights for your trading decisions."
                }
            ]
        },
        
        "final_cta": {
            "title": "Ready to See What the Data Says?",
            "subtitle": "Start with free signals. Track our results. Decide for yourself.",
            "cta_primary": "Create Free Account",
            "cta_secondary": "View Live Signal Tracker",
            "cta_secondary_link": "/track",
            "disclaimer": "No credit card required. Cancel anytime."
        },
        
        "footer": {
            "tagline": "An open experiment in AI trading signals",
            "disclaimer": "ELUXRAJ is not a registered investment advisor. All trading involves risk. Past performance does not guarantee future results. Only trade with capital you can afford to lose.",
            "links": {
                "Product": [
                    {"label": "Signal Tracker", "href": "/track"},
                    {"label": "How It Works", "href": "/api/v1/content/how-oracle-works"},
                    {"label": "Pricing", "href": "#pricing"},
                    {"label": "API Docs", "href": "/docs"}
                ],
                "Transparency": [
                    {"label": "Live Results", "href": "/track"},
                    {"label": "Methodology", "href": "/legal/methodology"},
                    {"label": "Limitations", "href": "/track/why-we-might-be-wrong"},
                    {"label": "Download Data", "href": "/api/v1/content/backtest-report"}
                ],
                "Company": [
                    {"label": "Team", "href": "/api/v1/content/team"},
                    {"label": "Contact", "href": "mailto:hello@eluxraj.ai"}
                ],
                "Legal": [
                    {"label": "Terms of Service", "href": "/legal/terms"},
                    {"label": "Privacy Policy", "href": "/legal/privacy"},
                    {"label": "Risk Disclaimer", "href": "/legal/disclaimer"}
                ]
            }
        }
    }


@router.get("/signal-card-example")
async def get_signal_card_example(db: Session = Depends(get_db)):
    """Get example signal card for homepage display"""
    
    # Get most recent signal or create example
    recent = db.query(Signal).order_by(Signal.created_at.desc()).first()
    
    if recent:
        return {
            "live": True,
            "signal": {
                "symbol": recent.symbol,
                "pair": recent.pair,
                "signal_type": recent.signal_type,
                "oracle_score": recent.oracle_score,
                "entry_price": recent.entry_price,
                "target_price": recent.target_price,
                "stop_loss": recent.stop_loss,
                "risk_reward": recent.risk_reward_ratio,
                "timeframe": recent.timeframe,
                "reasoning": recent.reasoning_summary,
                "factors": recent.reasoning_factors,
                "generated_at": recent.created_at.isoformat() if recent.created_at else None
            },
            "disclaimer": "This is a real signal from our system. Not a recommendation to trade."
        }
    else:
        return {
            "live": False,
            "signal": {
                "symbol": "BTC",
                "pair": "BTC/USDT",
                "signal_type": "buy",
                "oracle_score": 72,
                "entry_price": 95000.00,
                "target_price": 101000.00,
                "stop_loss": 92000.00,
                "risk_reward": 2.0,
                "timeframe": "48h",
                "reasoning": "Moderate BUY signal. 7-day uptrend intact. Volume surge detected. Market sentiment in fear zone — potential contrarian opportunity. Whale accumulation patterns observed.",
                "factors": {
                    "momentum_24h": "bullish",
                    "trend_7d": "uptrend",
                    "volume_flow": "high",
                    "market_sentiment": "fear",
                    "whale_activity": "accumulating"
                },
                "generated_at": datetime.utcnow().isoformat()
            },
            "disclaimer": "Example signal for illustration. Not a real recommendation."
        }


@router.get("/copy/headlines")
async def get_headline_variations():
    """Get multiple headline options (all compliant)"""
    return {
        "primary": [
            {
                "headline": "AI Trade Signals That Identify Profit Opportunities Before Most Traders Do",
                "subheadline": "Know what to buy, when to enter, and why — powered by institutional-style models, delivered in real time. No hype. Just data, logic, and risk clearly explained."
            },
            {
                "headline": "Trade Smarter with AI That Explains Its Reasoning",
                "subheadline": "Every signal comes with clear entry, target, stop-loss, and a full breakdown of why. No black boxes. No blind faith required."
            },
            {
                "headline": "Data-Driven Signals. Transparent Results. Honest Limitations.",
                "subheadline": "We publish every signal, track every outcome, and tell you exactly why we might be wrong. This is AI trading, done differently."
            }
        ],
        "avoid": [
            "❌ 'Guaranteed profits' - illegal claim",
            "❌ 'The same intelligence hedge funds use' - unverifiable",
            "❌ 'Never miss a trade' - impossible promise",
            "❌ 'Beat the market' - misleading",
            "❌ 'Risk-free' - nothing is risk-free"
        ],
        "best_practices": [
            "✓ Always include risk disclaimer near any performance claim",
            "✓ Use 'may', 'potential', 'historical' instead of absolute terms",
            "✓ Link to methodology and limitations",
            "✓ Show both wins AND losses",
            "✓ Be specific about what the product does, not what it promises"
        ]
    }
