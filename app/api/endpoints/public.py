from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from app.db.session import get_db
from app.models.signal import Signal

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def public_dashboard(db: Session = Depends(get_db)):
    """Public transparency dashboard - no login required"""
    
    # Get all stats
    total_signals = db.query(Signal).count()
    
    # Completed signals
    completed = db.query(Signal).filter(
        Signal.status.in_(["hit_target", "hit_stop", "expired"])
    ).all()
    
    active = db.query(Signal).filter(Signal.status == "active").count()
    
    # Calculate metrics
    wins = [s for s in completed if s.status == "hit_target"]
    losses = [s for s in completed if s.status in ["hit_stop", "expired"]]
    
    win_rate = round(len(wins) / len(completed) * 100, 1) if completed else 0
    loss_rate = round(len(losses) / len(completed) * 100, 1) if completed else 0
    
    returns = [s.outcome_pnl_percent for s in completed if s.outcome_pnl_percent is not None]
    avg_return = round(sum(returns) / len(returns), 2) if returns else 0
    total_return = round(sum(returns), 2) if returns else 0
    
    # Best and worst
    best = max(completed, key=lambda x: x.outcome_pnl_percent or -999) if completed else None
    worst = min(completed, key=lambda x: x.outcome_pnl_percent or 999) if completed else None
    
    # Recent signals
    recent = db.query(Signal).order_by(desc(Signal.created_at)).limit(20).all()
    
    # First signal date
    first = db.query(Signal).order_by(Signal.created_at.asc()).first()
    days_live = (datetime.utcnow() - first.created_at).days if first and first.created_at else 0
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ELUXRAJ - Public Signal Tracker</title>
        <meta name="description" content="Live, transparent tracking of every AI trading signal. See our wins, losses, and methodology.">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0a0a0f; color: #ccc; line-height: 1.6; }}
            .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
            
            /* Header */
            header {{ background: #12121a; border-bottom: 1px solid #333; padding: 20px 0; margin-bottom: 30px; }}
            header .container {{ display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px; }}
            .logo {{ font-size: 24px; font-weight: 700; background: linear-gradient(135deg, #7c3aed, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
            .header-links a {{ color: #888; text-decoration: none; margin-left: 20px; font-size: 14px; }}
            .header-links a:hover {{ color: #fff; }}
            
            /* Disclaimer Banner */
            .disclaimer-banner {{ background: linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(245, 158, 11, 0.15)); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 12px; padding: 20px; margin-bottom: 30px; text-align: center; }}
            .disclaimer-banner p {{ color: #f59e0b; font-size: 14px; margin: 0; }}
            .disclaimer-banner strong {{ color: #ef4444; }}
            
            /* Hero Stats */
            .hero {{ text-align: center; padding: 40px 0; }}
            .hero h1 {{ color: #fff; font-size: 32px; margin-bottom: 10px; }}
            .hero p {{ color: #888; font-size: 18px; margin-bottom: 30px; }}
            .live-badge {{ display: inline-flex; align-items: center; gap: 8px; background: rgba(34, 197, 94, 0.2); border: 1px solid rgba(34, 197, 94, 0.3); padding: 8px 16px; border-radius: 20px; font-size: 14px; color: #22c55e; margin-bottom: 20px; }}
            .live-badge .dot {{ width: 8px; height: 8px; background: #22c55e; border-radius: 50%; animation: pulse 2s infinite; }}
            @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.5; }} }}
            
            /* Stats Grid */
            .stats-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 40px; }}
            @media (max-width: 800px) {{ .stats-grid {{ grid-template-columns: repeat(2, 1fr); }} }}
            .stat-card {{ background: #12121a; border: 1px solid #333; border-radius: 12px; padding: 24px; text-align: center; }}
            .stat-card.highlight {{ border-color: #7c3aed; }}
            .stat-card .value {{ font-size: 36px; font-weight: 700; color: #fff; }}
            .stat-card .value.green {{ color: #22c55e; }}
            .stat-card .value.red {{ color: #ef4444; }}
            .stat-card .value.yellow {{ color: #f59e0b; }}
            .stat-card .label {{ color: #888; font-size: 12px; text-transform: uppercase; margin-top: 5px; letter-spacing: 1px; }}
            .stat-card .sublabel {{ color: #666; font-size: 11px; margin-top: 3px; }}
            
            /* Honest Box */
            .honest-box {{ background: #12121a; border: 2px solid #ef4444; border-radius: 16px; padding: 30px; margin-bottom: 40px; }}
            .honest-box h2 {{ color: #ef4444; font-size: 20px; margin-bottom: 20px; display: flex; align-items: center; gap: 10px; }}
            .honest-box ul {{ list-style: none; }}
            .honest-box li {{ padding: 10px 0; border-bottom: 1px solid #333; color: #ccc; display: flex; align-items: flex-start; gap: 10px; }}
            .honest-box li:last-child {{ border-bottom: none; }}
            .honest-box li::before {{ content: "⚠️"; }}
            
            /* Report Card */
            .report-card {{ background: #12121a; border: 1px solid #333; border-radius: 16px; padding: 30px; margin-bottom: 40px; }}
            .report-card h2 {{ color: #fff; margin-bottom: 20px; }}
            .report-row {{ display: flex; justify-content: space-between; padding: 15px 0; border-bottom: 1px solid #333; }}
            .report-row:last-child {{ border-bottom: none; }}
            .report-row .label {{ color: #888; }}
            .report-row .value {{ color: #fff; font-weight: 600; }}
            
            /* Signal Table */
            .signals-section {{ background: #12121a; border: 1px solid #333; border-radius: 16px; padding: 30px; margin-bottom: 40px; }}
            .signals-section h2 {{ color: #fff; margin-bottom: 20px; }}
            .signal-table {{ width: 100%; border-collapse: collapse; }}
            .signal-table th {{ text-align: left; padding: 12px; color: #888; font-size: 11px; text-transform: uppercase; border-bottom: 1px solid #333; }}
            .signal-table td {{ padding: 12px; border-bottom: 1px solid #222; }}
            .signal-table tr:hover {{ background: rgba(124, 58, 237, 0.05); }}
            .badge {{ padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; }}
            .badge.buy {{ background: rgba(34, 197, 94, 0.2); color: #22c55e; }}
            .badge.sell {{ background: rgba(239, 68, 68, 0.2); color: #ef4444; }}
            .badge.hold {{ background: rgba(245, 158, 11, 0.2); color: #f59e0b; }}
            .badge.active {{ background: rgba(59, 130, 246, 0.2); color: #3b82f6; }}
            .badge.hit_target {{ background: rgba(34, 197, 94, 0.2); color: #22c55e; }}
            .badge.hit_stop {{ background: rgba(239, 68, 68, 0.2); color: #ef4444; }}
            .badge.expired {{ background: rgba(107, 114, 128, 0.2); color: #6b7280; }}
            .pnl.positive {{ color: #22c55e; }}
            .pnl.negative {{ color: #ef4444; }}
            
            /* Methodology */
            .methodology {{ background: #12121a; border: 1px solid #333; border-radius: 16px; padding: 30px; margin-bottom: 40px; }}
            .methodology h2 {{ color: #fff; margin-bottom: 20px; }}
            .factor-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }}
            .factor {{ background: #1a1a2e; border-radius: 8px; padding: 15px; }}
            .factor .name {{ color: #fff; font-size: 14px; margin-bottom: 5px; }}
            .factor .weight {{ color: #7c3aed; font-size: 20px; font-weight: 700; }}
            .factor .desc {{ color: #888; font-size: 12px; }}
            
            /* Footer */
            footer {{ text-align: center; padding: 40px 20px; border-top: 1px solid #333; margin-top: 40px; }}
            footer p {{ color: #666; font-size: 14px; }}
            footer a {{ color: #7c3aed; text-decoration: none; }}
            
            /* Download buttons */
            .actions {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 20px; }}
            .btn {{ padding: 10px 20px; border-radius: 8px; text-decoration: none; font-size: 14px; font-weight: 600; }}
            .btn-primary {{ background: linear-gradient(135deg, #7c3aed, #06b6d4); color: #fff; }}
            .btn-secondary {{ background: rgba(255,255,255,0.1); color: #fff; }}
        </style>
    </head>
    <body>
        <header>
            <div class="container">
                <div class="logo">ELUXRAJ</div>
                <div class="header-links">
                    <a href="/api/v1/content/how-oracle-works">How It Works</a>
                    <a href="/api/v1/content/team">Team</a>
                    <a href="/legal/methodology">Methodology</a>
                    <a href="/docs">API Docs</a>
                </div>
            </div>
        </header>
        
        <div class="container">
            <!-- Disclaimer Banner -->
            <div class="disclaimer-banner">
                <p><strong>⚠️ NOT FINANCIAL ADVICE.</strong> ELUXRAJ provides informational AI signals only. Trading involves substantial risk. Past performance ≠ future results. <strong>Do not trade with money you cannot afford to lose.</strong></p>
            </div>
            
            <!-- Hero -->
            <div class="hero">
                <div class="live-badge"><span class="dot"></span> Live Signal Tracking</div>
                <h1>Radical Transparency</h1>
                <p>Every signal. Every outcome. No hiding.</p>
            </div>
            
            <!-- Stats -->
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="value">{days_live}</div>
                    <div class="label">Days Live</div>
                    <div class="sublabel">Since {first.created_at.strftime('%b %d, %Y') if first and first.created_at else 'N/A'}</div>
                </div>
                <div class="stat-card">
                    <div class="value">{total_signals}</div>
                    <div class="label">Total Signals</div>
                    <div class="sublabel">{active} currently active</div>
                </div>
                <div class="stat-card highlight">
                    <div class="value {'green' if win_rate > 50 else 'red' if win_rate < 50 else 'yellow'}">{win_rate}%</div>
                    <div class="label">Win Rate</div>
                    <div class="sublabel">{len(wins)} wins / {len(completed)} completed</div>
                </div>
                <div class="stat-card">
                    <div class="value {'green' if avg_return > 0 else 'red'}">{'+' if avg_return > 0 else ''}{avg_return}%</div>
                    <div class="label">Avg Return</div>
                    <div class="sublabel">Per completed signal</div>
                </div>
            </div>
            
            <!-- Honest Assessment -->
            <div class="honest-box">
                <h2>🚨 Why We Might Be Wrong</h2>
                <ul>
                    <li><strong>Limited track record:</strong> We've only been live for {days_live} days. That's not enough data to prove anything statistically significant.</li>
                    <li><strong>Simulated whale data:</strong> Our "whale tracking" currently uses pattern simulation, not real on-chain data. This is a known limitation.</li>
                    <li><strong>No black swan testing:</strong> Our model hasn't been tested during market crashes, flash crashes, or extreme volatility events.</li>
                    <li><strong>Public data only:</strong> We use CoinGecko and public sentiment data. We don't have access to order flow, institutional positioning, or insider information.</li>
                    <li><strong>Hindsight bias risk:</strong> We tuned our weights based on historical patterns. Past patterns may not repeat.</li>
                    <li><strong>No slippage/fee accounting:</strong> Our P&L calculations assume perfect execution at signal price. Real trading incurs fees and slippage.</li>
                    <li><strong>Solo project:</strong> This is built by one developer, not a team of PhDs. We're learning publicly.</li>
                </ul>
            </div>
            
            <!-- Report Card -->
            <div class="report-card">
                <h2>📊 Model Report Card</h2>
                <div class="report-row">
                    <span class="label">Total Signals Generated</span>
                    <span class="value">{total_signals}</span>
                </div>
                <div class="report-row">
                    <span class="label">Signals Completed (hit target/stop or expired)</span>
                    <span class="value">{len(completed)}</span>
                </div>
                <div class="report-row">
                    <span class="label">Signals That Hit Target 🎯</span>
                    <span class="value" style="color:#22c55e;">{len(wins)} ({win_rate}%)</span>
                </div>
                <div class="report-row">
                    <span class="label">Signals That Hit Stop Loss 🛑</span>
                    <span class="value" style="color:#ef4444;">{len([s for s in completed if s.status == 'hit_stop'])}</span>
                </div>
                <div class="report-row">
                    <span class="label">Signals That Expired ⏰</span>
                    <span class="value" style="color:#888;">{len([s for s in completed if s.status == 'expired'])}</span>
                </div>
                <div class="report-row">
                    <span class="label">Best Signal</span>
                    <span class="value" style="color:#22c55e;">{f"{best.symbol} +{best.outcome_pnl_percent:.1f}%" if best and best.outcome_pnl_percent else "N/A"}</span>
                </div>
                <div class="report-row">
                    <span class="label">Worst Signal</span>
                    <span class="value" style="color:#ef4444;">{f"{worst.symbol} {worst.outcome_pnl_percent:.1f}%" if worst and worst.outcome_pnl_percent else "N/A"}</span>
                </div>
                <div class="report-row">
                    <span class="label">Cumulative P&L (if all signals followed)</span>
                    <span class="value {'positive' if total_return > 0 else 'negative'}">{'+' if total_return > 0 else ''}{total_return}%</span>
                </div>
                
                <div class="actions">
                    <a href="/api/v1/content/backtest-report" class="btn btn-primary">📥 Download Full CSV</a>
                    <a href="/api/v1/transparency/signals" class="btn btn-secondary">🔗 API Access</a>
                    <a href="/api/v1/transparency/performance" class="btn btn-secondary">📊 Performance API</a>
                </div>
            </div>
            
            <!-- Open Methodology -->
            <div class="methodology">
                <h2>🔓 Open Methodology</h2>
                <p style="margin-bottom:20px;color:#888;">Here are the exact factors and weights we use. No secrets.</p>
                
                <div class="factor-grid">
                    <div class="factor">
                        <div class="weight">20%</div>
                        <div class="name">7-Day Trend</div>
                        <div class="desc">Price direction over past week</div>
                    </div>
                    <div class="factor">
                        <div class="weight">15%</div>
                        <div class="name">24h Momentum</div>
                        <div class="desc">Short-term price movement</div>
                    </div>
                    <div class="factor">
                        <div class="weight">15%</div>
                        <div class="name">Volume Flow</div>
                        <div class="desc">Volume vs market cap ratio</div>
                    </div>
                    <div class="factor">
                        <div class="weight">15%</div>
                        <div class="name">Market Sentiment</div>
                        <div class="desc">Fear & Greed Index (contrarian)</div>
                    </div>
                    <div class="factor">
                        <div class="weight">15%</div>
                        <div class="name">Whale Activity</div>
                        <div class="desc">Large holder patterns (simulated)</div>
                    </div>
                    <div class="factor">
                        <div class="weight">10%</div>
                        <div class="name">ATH Distance</div>
                        <div class="desc">Discount from all-time high</div>
                    </div>
                    <div class="factor">
                        <div class="weight">10%</div>
                        <div class="name">Volatility</div>
                        <div class="desc">24h price range (risk factor)</div>
                    </div>
                </div>
                
                <p style="margin-top:20px;color:#666;font-size:13px;">
                    <strong>Score Interpretation:</strong> Score ≥65 = BUY | Score 36-64 = HOLD | Score ≤35 = SELL<br>
                    <strong>Data Sources:</strong> CoinGecko API (prices), Alternative.me (sentiment)<br>
                    <strong>Model Version:</strong> oracle-v1.0.0
                </p>
            </div>
            
            <!-- Signal Log -->
            <div class="signals-section">
                <h2>📜 Recent Signals (All Public)</h2>
                <p style="color:#888;margin-bottom:20px;">Every signal is logged with timestamp. No cherry-picking. No hiding losses.</p>
                
                <div style="overflow-x:auto;">
                    <table class="signal-table">
                        <thead>
                            <tr>
                                <th>Time (UTC)</th>
                                <th>Symbol</th>
                                <th>Type</th>
                                <th>Score</th>
                                <th>Entry</th>
                                <th>Target</th>
                                <th>Stop</th>
                                <th>Status</th>
                                <th>P&L</th>
                            </tr>
                        </thead>
                        <tbody>
                            {"".join(f'''
                            <tr>
                                <td style="color:#888;font-size:13px;">{s.created_at.strftime('%m/%d %H:%M') if s.created_at else 'N/A'}</td>
                                <td><strong>{s.symbol}</strong></td>
                                <td><span class="badge {s.signal_type}">{s.signal_type.upper()}</span></td>
                                <td>{s.oracle_score}</td>
                                <td>${s.entry_price:,.2f}</td>
                                <td style="color:#22c55e;">${s.target_price:,.2f}</td>
                                <td style="color:#ef4444;">${s.stop_loss:,.2f}</td>
                                <td><span class="badge {s.status}">{s.status.replace('_', ' ').upper()}</span></td>
                                <td class="pnl {'positive' if s.outcome_pnl_percent and s.outcome_pnl_percent > 0 else 'negative' if s.outcome_pnl_percent else ''}">{f"{'+' if s.outcome_pnl_percent > 0 else ''}{s.outcome_pnl_percent:.1f}%" if s.outcome_pnl_percent else '—'}</td>
                            </tr>
                            ''' for s in recent)}
                        </tbody>
                    </table>
                </div>
                
                <div class="actions" style="margin-top:20px;">
                    <a href="/api/v1/transparency/signals?per_page=100" class="btn btn-secondary">View All Signals →</a>
                </div>
            </div>
        </div>
        
        <footer>
            <p>
                <strong>ELUXRAJ</strong> — An open experiment in AI trading signals.<br>
                <a href="/legal/terms">Terms</a> · <a href="/legal/privacy">Privacy</a> · <a href="/legal/disclaimer">Disclaimer</a> · <a href="/api/v1/content/how-oracle-works">Methodology</a><br><br>
                Built with radical transparency. <a href="https://github.com/" target="_blank">Open Source (Coming Soon)</a>
            </p>
        </footer>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@router.get("/api/report-card")
async def get_report_card(db: Session = Depends(get_db)):
    """API endpoint for report card data"""
    
    total_signals = db.query(Signal).count()
    completed = db.query(Signal).filter(Signal.status.in_(["hit_target", "hit_stop", "expired"])).all()
    active = db.query(Signal).filter(Signal.status == "active").count()
    
    wins = [s for s in completed if s.status == "hit_target"]
    stops = [s for s in completed if s.status == "hit_stop"]
    expired = [s for s in completed if s.status == "expired"]
    
    returns = [s.outcome_pnl_percent for s in completed if s.outcome_pnl_percent is not None]
    
    first = db.query(Signal).order_by(Signal.created_at.asc()).first()
    days_live = (datetime.utcnow() - first.created_at).days if first and first.created_at else 0
    
    return {
        "disclaimer": "Past performance does not guarantee future results. Not financial advice.",
        "generated_at": datetime.utcnow().isoformat(),
        "days_live": days_live,
        "start_date": first.created_at.isoformat() if first and first.created_at else None,
        "summary": {
            "total_signals": total_signals,
            "active": active,
            "completed": len(completed),
            "wins": len(wins),
            "hit_stop": len(stops),
            "expired": len(expired),
        },
        "performance": {
            "win_rate": round(len(wins) / len(completed) * 100, 1) if completed else 0,
            "loss_rate": round(len(stops) / len(completed) * 100, 1) if completed else 0,
            "avg_return_pct": round(sum(returns) / len(returns), 2) if returns else 0,
            "total_return_pct": round(sum(returns), 2) if returns else 0,
            "best_return": max(returns) if returns else 0,
            "worst_return": min(returns) if returns else 0,
        },
        "limitations": [
            f"Only {days_live} days of live data - not statistically significant",
            "Whale tracking uses simulated patterns, not real on-chain data",
            "No testing during black swan / extreme volatility events",
            "Uses public data only (CoinGecko, Fear & Greed Index)",
            "P&L does not account for slippage, fees, or execution delays",
            "Model weights tuned on historical data - hindsight bias risk",
        ],
        "methodology": {
            "model_version": "oracle-v1.0.0",
            "data_sources": ["CoinGecko API", "Alternative.me Fear & Greed"],
            "factors": {
                "7d_trend": 0.20,
                "24h_momentum": 0.15,
                "volume_flow": 0.15,
                "market_sentiment": 0.15,
                "whale_activity": 0.15,
                "ath_distance": 0.10,
                "volatility": 0.10,
            },
            "signal_thresholds": {
                "buy": "score >= 65",
                "hold": "36 <= score < 65",
                "sell": "score <= 35"
            }
        }
    }


@router.get("/why-we-might-be-wrong")
async def why_we_might_be_wrong(db: Session = Depends(get_db)):
    """Dedicated endpoint listing all known limitations"""
    
    first = db.query(Signal).order_by(Signal.created_at.asc()).first()
    days_live = (datetime.utcnow() - first.created_at).days if first and first.created_at else 0
    
    return {
        "title": "Why ELUXRAJ Might Be Wrong",
        "subtitle": "An honest assessment of our limitations",
        "last_updated": datetime.utcnow().isoformat(),
        "limitations": [
            {
                "category": "Track Record",
                "issue": f"Only {days_live} days of live signals",
                "why_it_matters": "Statistical significance typically requires months or years of data. Our sample size is too small to draw reliable conclusions.",
                "what_we_are_doing": "Building track record publicly. Every signal logged."
            },
            {
                "category": "Data Quality",
                "issue": "Whale tracking is simulated",
                "why_it_matters": "Our 'whale activity' factor uses pattern simulation, not real blockchain data. This reduces signal accuracy.",
                "what_we_are_doing": "Integrating Whale Alert API in Q1 2025."
            },
            {
                "category": "Market Conditions",
                "issue": "No black swan testing",
                "why_it_matters": "Our model hasn't experienced a major crash, flash crash, or extreme volatility. It may fail catastrophically in such conditions.",
                "what_we_are_doing": "Historical backtesting on 2020-2022 crash data planned."
            },
            {
                "category": "Data Sources",
                "issue": "Public data only",
                "why_it_matters": "We use CoinGecko and public sentiment. We don't have order flow, OTC data, or institutional positioning that real hedge funds use.",
                "what_we_are_doing": "This is a fundamental limitation of retail tools."
            },
            {
                "category": "Execution",
                "issue": "No slippage/fee accounting",
                "why_it_matters": "Our P&L assumes perfect execution at signal price. Real trading incurs 0.1-0.5% fees and potential slippage.",
                "what_we_are_doing": "Adding fee-adjusted returns in next update."
            },
            {
                "category": "Model Risk",
                "issue": "Overfitting / hindsight bias",
                "why_it_matters": "We tuned our factor weights on historical data. These patterns may not repeat. All backtests look better than live trading.",
                "what_we_are_doing": "Publishing methodology openly for scrutiny."
            },
            {
                "category": "Team",
                "issue": "Solo developer project",
                "why_it_matters": "This isn't built by a team of PhDs or ex-hedge fund quants. It's one developer learning in public.",
                "what_we_are_doing": "Seeking advisors and contributors."
            },
            {
                "category": "Regulatory",
                "issue": "Not registered or audited",
                "why_it_matters": "We're not SEC/CFTC registered. No third-party audit yet. You have to trust our self-reported numbers.",
                "what_we_are_doing": "Preparing for third-party audit."
            }
        ],
        "our_commitment": [
            "We will never hide losing signals",
            "We will publish methodology changes",
            "We will acknowledge when we're wrong",
            "We will not guarantee returns"
        ]
    }
