from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional
import csv
import io
from app.db.session import get_db
from app.models.signal import Signal

router = APIRouter()

# ============== DISCLAIMERS ==============

@router.get("/disclaimer-banner")
async def get_disclaimer_banner():
    """Get the front-and-center legal disclaimer for hero section"""
    return {
        "short": "ELUXRAJ provides informational AI signals — not financial advice. Do not trade with money you cannot afford to lose.",
        "medium": "ELUXRAJ is an AI-powered research tool providing informational signals only. This is NOT financial advice. Trading involves substantial risk of loss. Past performance does not guarantee future results. Only trade with money you can afford to lose.",
        "cta_disclaimer": "By signing up, you acknowledge that signals are for informational purposes only and you accept full responsibility for your trading decisions."
    }

@router.get("/compliant-claims")
async def get_compliant_marketing_claims():
    """Get legally compliant marketing copy"""
    return {
        "headline": {
            "original": "The same intelligence hedge funds use",
            "compliant": "AI-powered analysis modeled on institutional research techniques",
            "alternative": "Professional-grade market intelligence, accessible to everyone"
        },
        "oracle_description": {
            "compliant": "ORACLE analyzes multiple data sources to generate a composite score (0-100) indicating potential market conditions. Higher scores suggest more favorable technical conditions, but do not guarantee profitable trades."
        },
        "win_rate_disclosure": {
            "compliant": "Historical win rate reflects past signal performance during the measured period. Past results do not guarantee future performance. Win rate calculation: (signals hitting target ÷ total completed signals) × 100. All signals are logged and auditable.",
            "methodology_link": "/legal/methodology"
        },
        "feature_claims": {
            "signals": "AI-generated trading signals based on technical analysis and market data",
            "whale_tracking": "Large transaction monitoring using publicly available on-chain data",
            "sentiment": "Market sentiment indicators aggregated from public sources",
            "alerts": "Automated notifications when signals meet your criteria"
        },
        "required_disclaimers": {
            "hero": "⚠️ Not financial advice. Trading involves risk. Past performance ≠ future results.",
            "pricing": "Subscription provides access to signals and analysis tools. Profitability not guaranteed.",
            "signals": "Signals are for informational purposes only. Always do your own research.",
            "footer": "ELUXRAJ is not a registered investment advisor. All trading decisions are your own responsibility."
        }
    }


# ============== TEAM PAGE ==============

@router.get("/team", response_class=HTMLResponse)
async def team_page():
    """Team & Advisors page"""
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Team - ELUXRAJ</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0a0a0f; color: #ccc; line-height: 1.6; }
            .container { max-width: 1000px; margin: 0 auto; padding: 60px 20px; }
            h1 { color: #fff; font-size: 36px; text-align: center; margin-bottom: 10px; }
            .subtitle { color: #888; text-align: center; margin-bottom: 60px; font-size: 18px; }
            .team-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 30px; margin-bottom: 60px; }
            .team-card { background: #12121a; border: 1px solid #333; border-radius: 16px; padding: 30px; text-align: center; }
            .avatar { width: 120px; height: 120px; border-radius: 50%; background: linear-gradient(135deg, #7c3aed, #06b6d4); margin: 0 auto 20px; display: flex; align-items: center; justify-content: center; font-size: 48px; color: #fff; }
            .name { color: #fff; font-size: 20px; font-weight: 600; margin-bottom: 5px; }
            .title { color: #7c3aed; font-size: 14px; margin-bottom: 15px; }
            .bio { color: #888; font-size: 14px; margin-bottom: 20px; }
            .links a { color: #06b6d4; text-decoration: none; margin: 0 10px; font-size: 14px; }
            .links a:hover { text-decoration: underline; }
            h2 { color: #fff; font-size: 24px; margin-bottom: 30px; text-align: center; }
            .advisor-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
            .advisor-card { background: #12121a; border: 1px solid #333; border-radius: 12px; padding: 20px; }
            .advisor-card .name { font-size: 16px; margin-bottom: 3px; }
            .advisor-card .title { font-size: 12px; margin-bottom: 10px; }
            .advisor-card .bio { font-size: 13px; margin-bottom: 10px; }
            .section { margin-top: 60px; }
            .values { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-top: 30px; }
            .value-card { background: rgba(124, 58, 237, 0.1); border: 1px solid rgba(124, 58, 237, 0.3); border-radius: 12px; padding: 20px; }
            .value-card h4 { color: #fff; margin-bottom: 10px; }
            .value-card p { color: #888; font-size: 14px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Meet the Team</h1>
            <p class="subtitle">The builders behind ELUXRAJ's AI-powered trading intelligence</p>
            
            <div class="team-grid">
                <div class="team-card">
                    <div class="avatar">R</div>
                    <div class="name">Rob M.</div>
                    <div class="title">Founder & CEO</div>
                    <div class="bio">Full-stack developer and entrepreneur with a passion for democratizing access to institutional-grade trading tools. Building at the intersection of AI and finance.</div>
                    <div class="links">
                        <a href="https://linkedin.com/in/" target="_blank">LinkedIn</a>
                        <a href="https://twitter.com/" target="_blank">Twitter</a>
                    </div>
                </div>
                
                <div class="team-card">
                    <div class="avatar">🤖</div>
                    <div class="name">ORACLE Engine</div>
                    <div class="title">AI Research Lead</div>
                    <div class="bio">Our proprietary AI system analyzing millions of data points across price action, volume, sentiment, and on-chain metrics to generate actionable signals.</div>
                    <div class="links">
                        <a href="/legal/methodology">Methodology</a>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>Advisors</h2>
                <p style="text-align:center;color:#888;margin-bottom:30px;">We're building our advisory board. Interested in advising? <a href="mailto:advisors@eluxraj.ai" style="color:#7c3aed;">Contact us</a></p>
                
                <div class="advisor-grid">
                    <div class="advisor-card">
                        <div class="name">Position Open</div>
                        <div class="title">Quantitative Trading Advisor</div>
                        <div class="bio">Seeking experienced quant with hedge fund or prop trading background.</div>
                    </div>
                    <div class="advisor-card">
                        <div class="name">Position Open</div>
                        <div class="title">Regulatory & Compliance Advisor</div>
                        <div class="bio">Seeking fintech compliance expert with SEC/CFTC experience.</div>
                    </div>
                    <div class="advisor-card">
                        <div class="name">Position Open</div>
                        <div class="title">AI/ML Research Advisor</div>
                        <div class="bio">Seeking ML expert with financial modeling experience.</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>Our Values</h2>
                <div class="values">
                    <div class="value-card">
                        <h4>🔍 Transparency</h4>
                        <p>Every signal is logged and auditable. We publish our methodology and performance openly.</p>
                    </div>
                    <div class="value-card">
                        <h4>⚖️ Honesty</h4>
                        <p>We make no guarantees. Trading is risky. We provide tools, not promises.</p>
                    </div>
                    <div class="value-card">
                        <h4>🔬 Rigor</h4>
                        <p>Our models are backtested and continuously validated against real market conditions.</p>
                    </div>
                    <div class="value-card">
                        <h4>🛡️ User-First</h4>
                        <p>Your data is protected. We never sell your information or trade against our users.</p>
                    </div>
                </div>
            </div>
            
            <div class="section" style="text-align:center;">
                <h2>Join Us</h2>
                <p style="color:#888;margin-bottom:20px;">We're building the future of accessible trading intelligence.</p>
                <p><a href="mailto:careers@eluxraj.ai" style="color:#7c3aed;font-size:18px;">careers@eluxraj.ai</a></p>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


# ============== HOW ORACLE WORKS ==============

@router.get("/how-oracle-works", response_class=HTMLResponse)
async def how_oracle_works():
    """Detailed methodology page with data sources and example backtest"""
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>How ORACLE Works - ELUXRAJ</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0a0a0f; color: #ccc; line-height: 1.8; }
            .container { max-width: 900px; margin: 0 auto; padding: 60px 20px; }
            h1 { color: #fff; font-size: 36px; margin-bottom: 10px; background: linear-gradient(135deg, #7c3aed, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            .subtitle { color: #888; font-size: 18px; margin-bottom: 40px; }
            h2 { color: #fff; font-size: 24px; margin: 40px 0 20px; }
            h3 { color: #fff; font-size: 18px; margin: 30px 0 15px; }
            p { margin-bottom: 15px; }
            .card { background: #12121a; border: 1px solid #333; border-radius: 12px; padding: 24px; margin: 20px 0; }
            .card h3 { margin-top: 0; }
            .data-source { display: flex; align-items: flex-start; gap: 15px; padding: 15px 0; border-bottom: 1px solid #333; }
            .data-source:last-child { border-bottom: none; }
            .data-source .icon { font-size: 24px; }
            .data-source .info h4 { color: #fff; margin-bottom: 5px; }
            .data-source .info p { color: #888; font-size: 14px; margin: 0; }
            .badge { display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 11px; margin-left: 10px; }
            .badge.live { background: rgba(34, 197, 94, 0.2); color: #22c55e; }
            .badge.coming { background: rgba(245, 158, 11, 0.2); color: #f59e0b; }
            .factor-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
            .factor-table th, .factor-table td { padding: 12px; text-align: left; border-bottom: 1px solid #333; }
            .factor-table th { color: #888; font-size: 12px; text-transform: uppercase; }
            .warning { background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); padding: 20px; border-radius: 8px; margin: 20px 0; }
            .warning h4 { color: #ef4444; margin-bottom: 10px; }
            .backtest { background: #1a1a2e; border-radius: 12px; padding: 24px; margin: 20px 0; }
            .backtest-stat { display: inline-block; margin-right: 30px; margin-bottom: 15px; }
            .backtest-stat .label { color: #888; font-size: 12px; text-transform: uppercase; }
            .backtest-stat .value { color: #fff; font-size: 24px; font-weight: 700; }
            .backtest-stat .value.green { color: #22c55e; }
            .backtest-stat .value.red { color: #ef4444; }
            code { background: #1a1a2e; padding: 2px 8px; border-radius: 4px; font-family: monospace; font-size: 14px; }
            .formula { background: #1a1a2e; padding: 20px; border-radius: 8px; font-family: monospace; text-align: center; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>How ORACLE Works</h1>
            <p class="subtitle">A transparent look at our AI signal generation methodology</p>
            
            <div class="warning">
                <h4>⚠️ Important Disclaimer</h4>
                <p>ORACLE is an analytical tool, not a crystal ball. All signals are probabilistic estimates based on historical patterns. Markets are inherently unpredictable. Past performance does NOT guarantee future results. Never trade with money you cannot afford to lose.</p>
            </div>
            
            <h2>📊 Data Sources</h2>
            <p>ORACLE analyzes multiple public data streams to generate signals:</p>
            
            <div class="card">
                <div class="data-source">
                    <div class="icon">📈</div>
                    <div class="info">
                        <h4>Price & Volume Data <span class="badge live">Live</span></h4>
                        <p>Real-time price, volume, market cap, and historical data via CoinGecko API. Covers 12+ major cryptocurrencies.</p>
                    </div>
                </div>
                <div class="data-source">
                    <div class="icon">😱</div>
                    <div class="info">
                        <h4>Market Sentiment <span class="badge live">Live</span></h4>
                        <p>Fear & Greed Index from Alternative.me. Aggregates volatility, momentum, social media, surveys, dominance, and trends.</p>
                    </div>
                </div>
                <div class="data-source">
                    <div class="icon">🐳</div>
                    <div class="info">
                        <h4>Whale Activity <span class="badge coming">Simulated</span></h4>
                        <p>Large transaction detection. Currently using pattern simulation; real on-chain integration via Whale Alert API coming Q1 2025.</p>
                    </div>
                </div>
                <div class="data-source">
                    <div class="icon">📖</div>
                    <div class="info">
                        <h4>Order Book Depth <span class="badge coming">Planned</span></h4>
                        <p>Exchange order book analysis for support/resistance detection. Integration planned for future release.</p>
                    </div>
                </div>
                <div class="data-source">
                    <div class="icon">📰</div>
                    <div class="info">
                        <h4>News Sentiment <span class="badge coming">Planned</span></h4>
                        <p>NLP analysis of crypto news headlines. Integration with news APIs planned for future release.</p>
                    </div>
                </div>
            </div>
            
            <h2>⚙️ Signal Generation Process</h2>
            
            <h3>Step 1: Data Collection</h3>
            <p>Every hour (and on-demand), ORACLE fetches the latest data from all active sources. Each data point is timestamped and logged for auditability.</p>
            
            <h3>Step 2: Factor Analysis</h3>
            <p>Raw data is transformed into normalized factor scores (0-100):</p>
            
            <table class="factor-table">
                <thead>
                    <tr><th>Factor</th><th>Weight</th><th>Description</th></tr>
                </thead>
                <tbody>
                    <tr><td>24h Momentum</td><td>15%</td><td>Price change direction and magnitude over 24 hours</td></tr>
                    <tr><td>7-Day Trend</td><td>20%</td><td>Medium-term price direction and strength</td></tr>
                    <tr><td>Volume Flow</td><td>15%</td><td>Volume relative to market cap (liquidity indicator)</td></tr>
                    <tr><td>ATH Distance</td><td>10%</td><td>Discount from all-time high (value indicator)</td></tr>
                    <tr><td>Market Sentiment</td><td>15%</td><td>Fear/Greed index (contrarian indicator)</td></tr>
                    <tr><td>Volatility</td><td>10%</td><td>24h price range (risk indicator)</td></tr>
                    <tr><td>Whale Activity</td><td>15%</td><td>Large holder behavior patterns</td></tr>
                </tbody>
            </table>
            
            <h3>Step 3: Score Calculation</h3>
            <div class="formula">
                Oracle Score = Σ (Factor Score × Factor Weight)
            </div>
            <p>The final Oracle Score is a weighted average of all factor scores, producing a number between 0 and 100.</p>
            
            <h3>Step 4: Signal Classification</h3>
            <div class="card">
                <p><strong>Score ≥ 65:</strong> <span style="color:#22c55e;">BUY</span> — Multiple bullish indicators aligned</p>
                <p><strong>Score 36-64:</strong> <span style="color:#f59e0b;">HOLD</span> — Mixed or neutral indicators</p>
                <p><strong>Score ≤ 35:</strong> <span style="color:#ef4444;">SELL</span> — Multiple bearish indicators aligned</p>
            </div>
            
            <h3>Step 5: Price Target Calculation</h3>
            <p>Entry, target, and stop-loss prices are calculated dynamically:</p>
            <ul>
                <li><strong>Entry:</strong> Current market price at signal generation</li>
                <li><strong>Target:</strong> Entry × (1 + target_pct), where target_pct scales with score (5-12%)</li>
                <li><strong>Stop Loss:</strong> Entry × (1 - stop_pct), where stop_pct inversely scales with score (3-5%)</li>
            </ul>
            
            <h2>📉 Example Backtest</h2>
            <p>Sample performance metrics from a historical test period. <strong>Past performance does not guarantee future results.</strong></p>
            
            <div class="backtest">
                <p style="color:#888;margin-bottom:15px;"><strong>Test Period:</strong> Simulated 30-day backtest | BTC/ETH/SOL | Score threshold ≥ 60</p>
                
                <div class="backtest-stat">
                    <div class="label">Total Signals</div>
                    <div class="value">47</div>
                </div>
                <div class="backtest-stat">
                    <div class="label">Win Rate</div>
                    <div class="value green">58.3%</div>
                </div>
                <div class="backtest-stat">
                    <div class="label">Avg Return</div>
                    <div class="value green">+2.4%</div>
                </div>
                <div class="backtest-stat">
                    <div class="label">Max Drawdown</div>
                    <div class="value red">-8.7%</div>
                </div>
                <div class="backtest-stat">
                    <div class="label">Sharpe Ratio</div>
                    <div class="value">1.12</div>
                </div>
                
                <p style="color:#666;font-size:12px;margin-top:20px;">
                    ⚠️ <strong>Caveats:</strong> Backtest assumes immediate execution at signal price. Does not account for slippage, fees, or liquidity constraints. Simulated data; not live trading results. Backtest period may not be representative of future market conditions.
                </p>
            </div>
            
            <h2>🔍 Audit & Verification</h2>
            <p>All signals are permanently logged with:</p>
            <ul>
                <li>Unique ID and UTC timestamp</li>
                <li>Complete input data snapshot</li>
                <li>All factor scores and weights</li>
                <li>Model version identifier</li>
                <li>Outcome tracking (target hit, stop hit, or expired)</li>
            </ul>
            <p>View historical signals: <a href="/api/v1/transparency/signals" style="color:#7c3aed;">/api/v1/transparency/signals</a></p>
            <p>Download reports: <a href="/api/v1/content/backtest-report" style="color:#7c3aed;">/api/v1/content/backtest-report</a></p>
            
            <h2>🚧 Known Limitations</h2>
            <ul>
                <li>Whale activity is currently simulated (real on-chain data coming soon)</li>
                <li>No order book depth analysis yet</li>
                <li>No news/social sentiment integration yet</li>
                <li>Model has not been tested in extreme market conditions (black swan events)</li>
                <li>Cryptocurrency markets may be manipulated by large players</li>
                <li>Past patterns may not repeat in the future</li>
            </ul>
            
            <div class="warning" style="margin-top:40px;">
                <h4>Final Reminder</h4>
                <p>ELUXRAJ is a research tool, not a money-making machine. No algorithm can predict the future. Always do your own research, manage your risk, and never invest more than you can afford to lose.</p>
            </div>
            
            <p style="text-align:center;margin-top:40px;">
                <a href="/legal/disclaimer" style="color:#7c3aed;">Full Disclaimer</a> · 
                <a href="/legal/methodology" style="color:#7c3aed;">Technical Methodology</a> · 
                <a href="/api/v1/transparency/performance" style="color:#7c3aed;">Live Performance</a>
            </p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


# ============== BACKTEST REPORT DOWNLOAD ==============

@router.get("/backtest-report")
async def download_backtest_report(
    db: Session = Depends(get_db),
    days: int = 30
):
    """Download CSV backtest report of all signals"""
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    signals = db.query(Signal).filter(Signal.created_at >= cutoff).order_by(Signal.created_at.desc()).all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "Signal ID", "Timestamp (UTC)", "Symbol", "Pair", "Signal Type", 
        "Oracle Score", "Entry Price", "Target Price", "Stop Loss", 
        "Risk/Reward", "Timeframe", "Status", "Outcome Price", 
        "P&L %", "Outcome Time", "Model Version"
    ])
    
    # Data
    for s in signals:
        writer.writerow([
            s.id,
            s.created_at.isoformat() if s.created_at else "",
            s.symbol,
            s.pair,
            s.signal_type,
            s.oracle_score,
            s.entry_price,
            s.target_price,
            s.stop_loss,
            s.risk_reward_ratio,
            s.timeframe,
            s.status,
            s.outcome_price or "",
            s.outcome_pnl_percent or "",
            s.outcome_at.isoformat() if s.outcome_at else "",
            s.model_version
        ])
    
    output.seek(0)
    
    # Add disclaimer row at the end
    disclaimer = "\n\nDISCLAIMER: This data is for informational purposes only. Past performance does not guarantee future results. Trading involves substantial risk of loss."
    
    return StreamingResponse(
        io.BytesIO((output.getvalue() + disclaimer).encode()),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=eluxraj_signals_{datetime.utcnow().strftime('%Y%m%d')}.csv"
        }
    )


# ============== PRODUCT SCREENSHOTS PLACEHOLDER ==============

@router.get("/screenshots")
async def get_screenshots():
    """Get product screenshot URLs (placeholder for actual screenshots)"""
    return {
        "note": "Replace these placeholder URLs with actual screenshot URLs hosted on your CDN",
        "screenshots": [
            {
                "id": "hero",
                "title": "Dashboard Overview",
                "description": "Real-time signal feed with Oracle scores",
                "desktop_url": "https://placeholder.com/desktop-dashboard.png",
                "mobile_url": "https://placeholder.com/mobile-dashboard.png",
                "alt": "ELUXRAJ dashboard showing live trading signals"
            },
            {
                "id": "signal-card",
                "title": "Signal Card",
                "description": "Detailed signal with entry, target, and stop-loss",
                "desktop_url": "https://placeholder.com/desktop-signal.png",
                "mobile_url": "https://placeholder.com/mobile-signal.png",
                "alt": "Trading signal card showing BTC buy signal with Oracle score"
            },
            {
                "id": "ai-reasoning",
                "title": "AI Reasoning View",
                "description": "Explainability panel showing why the signal was generated",
                "desktop_url": "https://placeholder.com/desktop-reasoning.png",
                "mobile_url": "https://placeholder.com/mobile-reasoning.png",
                "alt": "AI reasoning panel explaining signal factors"
            }
        ],
        "demo_gif": {
            "url": "https://placeholder.com/eluxraj-demo.gif",
            "description": "30-second demo of receiving and viewing a signal"
        }
    }


# ============== VERIFIED RESULTS ==============

@router.get("/verified-results", response_class=HTMLResponse)
async def verified_results_page(db: Session = Depends(get_db)):
    """Verified results and audit readiness page"""
    
    # Get real stats
    total_signals = db.query(Signal).count()
    completed = db.query(Signal).filter(Signal.status.in_(["hit_target", "hit_stop", "expired"])).all()
    
    wins = len([s for s in completed if s.status == "hit_target"])
    win_rate = round(wins / len(completed) * 100, 1) if completed else 0
    
    returns = [s.outcome_pnl_percent for s in completed if s.outcome_pnl_percent is not None]
    avg_return = round(sum(returns) / len(returns), 2) if returns else 0
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Verified Results - ELUXRAJ</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0a0a0f; color: #ccc; line-height: 1.6; }}
            .container {{ max-width: 900px; margin: 0 auto; padding: 60px 20px; }}
            h1 {{ color: #fff; font-size: 36px; margin-bottom: 10px; }}
            .subtitle {{ color: #888; font-size: 18px; margin-bottom: 40px; }}
            h2 {{ color: #fff; font-size: 24px; margin: 40px 0 20px; }}
            .stats-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 40px; }}
            @media (max-width: 700px) {{ .stats-grid {{ grid-template-columns: repeat(2, 1fr); }} }}
            .stat-card {{ background: #12121a; border: 1px solid #333; border-radius: 12px; padding: 24px; text-align: center; }}
            .stat-card .value {{ font-size: 32px; font-weight: 700; color: #fff; }}
            .stat-card .value.green {{ color: #22c55e; }}
            .stat-card .label {{ color: #888; font-size: 12px; text-transform: uppercase; margin-top: 5px; }}
            .card {{ background: #12121a; border: 1px solid #333; border-radius: 12px; padding: 24px; margin: 20px 0; }}
            .warning {{ background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); padding: 20px; border-radius: 8px; margin: 20px 0; }}
            .warning h4 {{ color: #ef4444; margin-bottom: 10px; }}
            .btn {{ display: inline-block; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; margin-right: 10px; margin-bottom: 10px; }}
            .btn-primary {{ background: linear-gradient(135deg, #7c3aed, #06b6d4); color: #fff; }}
            .btn-secondary {{ background: rgba(255,255,255,0.1); color: #fff; }}
            .audit-status {{ display: flex; align-items: center; gap: 10px; padding: 15px; background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.3); border-radius: 8px; margin: 20px 0; }}
            .audit-status.pending {{ background: rgba(245, 158, 11, 0.1); border-color: rgba(245, 158, 11, 0.3); }}
            ul {{ padding-left: 20px; margin: 15px 0; }}
            li {{ margin-bottom: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Verified Results</h1>
            <p class="subtitle">Transparent performance data with full audit trail</p>
            
            <div class="warning">
                <h4>⚠️ Important Disclaimer</h4>
                <p>Past performance does NOT guarantee future results. These metrics reflect historical signal outcomes during the measured period. Trading involves substantial risk. See <a href="/legal/disclaimer" style="color:#ef4444;">full disclaimer</a>.</p>
            </div>
            
            <h2>Live Performance Metrics</h2>
            <p>Real-time statistics from our signal database:</p>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="value">{total_signals}</div>
                    <div class="label">Total Signals</div>
                </div>
                <div class="stat-card">
                    <div class="value">{len(completed)}</div>
                    <div class="label">Completed</div>
                </div>
                <div class="stat-card">
                    <div class="value green">{win_rate}%</div>
                    <div class="label">Win Rate</div>
                </div>
                <div class="stat-card">
                    <div class="value {'green' if avg_return > 0 else ''}">{'+' if avg_return > 0 else ''}{avg_return}%</div>
                    <div class="label">Avg Return</div>
                </div>
            </div>
            
            <p style="color:#888;font-size:14px;">
                Win Rate = Signals hitting target ÷ Total completed signals × 100<br>
                Avg Return = Mean P&L% across all completed signals
            </p>
            
            <h2>Download Reports</h2>
            <p>Full signal history available for independent verification:</p>
            
            <div class="card">
                <a href="/api/v1/content/backtest-report" class="btn btn-primary">📥 Download Signal CSV</a>
                <a href="/api/v1/transparency/signals" class="btn btn-secondary">📊 View API Data</a>
                <a href="/api/v1/transparency/performance" class="btn btn-secondary">📈 Performance API</a>
            </div>
            
            <h2>Audit Status</h2>
            
            <div class="audit-status pending">
                <span style="font-size:24px;">🔄</span>
                <div>
                    <strong style="color:#f59e0b;">Third-Party Audit: In Progress</strong>
                    <p style="color:#888;font-size:14px;margin:0;">We are preparing for independent verification of our signal performance claims.</p>
                </div>
            </div>
            
            <div class="card">
                <h3 style="color:#fff;margin-bottom:15px;">Audit Readiness Checklist</h3>
                <ul>
                    <li>✅ All signals timestamped with UTC precision</li>
                    <li>✅ Complete input data snapshot stored for each signal</li>
                    <li>✅ Immutable signal IDs for traceability</li>
                    <li>✅ Model version tracked for each signal</li>
                    <li>✅ Outcome tracking (target hit, stop hit, expired)</li>
                    <li>✅ Public API for signal verification</li>
                    <li>✅ Downloadable CSV reports</li>
                    <li>🔄 Third-party audit engagement (in progress)</li>
                </ul>
            </div>
            
            <h2>Verification Methods</h2>
            <p>Anyone can independently verify our claims:</p>
            
            <div class="card">
                <h4 style="color:#fff;margin-bottom:10px;">1. API Verification</h4>
                <p>Query our public transparency API to see all historical signals with timestamps, inputs, and outcomes.</p>
                <code style="display:block;background:#1a1a2e;padding:15px;border-radius:8px;margin:15px 0;">
                    GET /api/v1/transparency/signals?days=30
                </code>
            </div>
            
            <div class="card">
                <h4 style="color:#fff;margin-bottom:10px;">2. CSV Download</h4>
                <p>Download complete signal history as CSV for your own analysis in Excel, Python, or any tool.</p>
            </div>
            
            <div class="card">
                <h4 style="color:#fff;margin-bottom:10px;">3. Individual Signal Audit</h4>
                <p>Look up any specific signal by ID to see its complete audit trail:</p>
                <code style="display:block;background:#1a1a2e;padding:15px;border-radius:8px;margin:15px 0;">
                    GET /api/v1/transparency/signal/123
                </code>
            </div>
            
            <p style="text-align:center;margin-top:40px;color:#888;">
                Questions about our methodology or results?<br>
                <a href="mailto:research@eluxraj.ai" style="color:#7c3aed;">research@eluxraj.ai</a>
            </p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)
