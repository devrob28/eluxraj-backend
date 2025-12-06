from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from datetime import datetime

router = APIRouter()

@router.get("/terms", response_class=HTMLResponse)
async def terms_of_service():
    """Terms of Service"""
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Terms of Service - ELUXRAJ</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0a0a0f; color: #ccc; line-height: 1.8; }
            .container { max-width: 800px; margin: 0 auto; padding: 40px 20px; }
            h1 { color: #fff; font-size: 32px; margin-bottom: 10px; background: linear-gradient(135deg, #7c3aed, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            h2 { color: #fff; font-size: 20px; margin: 30px 0 15px; }
            p, li { margin-bottom: 15px; }
            ul { padding-left: 20px; }
            .updated { color: #888; font-size: 14px; margin-bottom: 30px; }
            a { color: #7c3aed; }
            .warning { background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); padding: 20px; border-radius: 8px; margin: 20px 0; }
            .warning h3 { color: #ef4444; margin-bottom: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Terms of Service</h1>
            <p class="updated">Last Updated: """ + datetime.utcnow().strftime("%B %d, %Y") + """</p>
            
            <div class="warning">
                <h3>⚠️ Important Investment Disclaimer</h3>
                <p>ELUXRAJ provides AI-generated trading signals for informational purposes only. These signals do NOT constitute financial advice, investment recommendations, or solicitations to buy or sell any securities or cryptocurrencies. Trading involves substantial risk of loss. Past performance does not guarantee future results.</p>
            </div>
            
            <h2>1. Acceptance of Terms</h2>
            <p>By accessing or using ELUXRAJ ("Service"), you agree to be bound by these Terms of Service. If you do not agree to these terms, do not use the Service.</p>
            
            <h2>2. Description of Service</h2>
            <p>ELUXRAJ is an AI-powered platform that provides:</p>
            <ul>
                <li>Automated trading signal generation using machine learning algorithms</li>
                <li>Market sentiment analysis and fear/greed indicators</li>
                <li>Technical analysis and price target suggestions</li>
                <li>Educational content about trading and market dynamics</li>
            </ul>
            
            <h2>3. No Financial Advice</h2>
            <p>The information provided by ELUXRAJ is for general informational and educational purposes only. It is NOT:</p>
            <ul>
                <li>Financial, investment, legal, or tax advice</li>
                <li>A recommendation to buy, sell, or hold any asset</li>
                <li>A solicitation to engage in any investment activity</li>
                <li>A guarantee of any specific outcome or return</li>
            </ul>
            <p>You should consult with a qualified financial advisor before making any investment decisions.</p>
            
            <h2>4. Risk Acknowledgment</h2>
            <p>By using this Service, you acknowledge that:</p>
            <ul>
                <li>Trading cryptocurrencies and securities involves substantial risk of loss</li>
                <li>You may lose some or all of your invested capital</li>
                <li>Past performance of signals does not guarantee future results</li>
                <li>AI predictions are probabilistic and not guaranteed</li>
                <li>Market conditions can change rapidly and unpredictably</li>
                <li>You are solely responsible for your own trading decisions</li>
            </ul>
            
            <h2>5. Subscription & Payments</h2>
            <p>ELUXRAJ offers tiered subscription plans:</p>
            <ul>
                <li><strong>Free:</strong> Limited signals, delayed data, basic assets only</li>
                <li><strong>Pro ($98/month):</strong> Real-time signals, all assets, full analysis</li>
                <li><strong>Elite ($197/month):</strong> Priority signals, market scanning, whale intelligence, email alerts</li>
            </ul>
            <p>Subscriptions renew automatically. You may cancel at any time. Refunds are provided according to our refund policy.</p>
            
            <h2>6. User Conduct</h2>
            <p>You agree NOT to:</p>
            <ul>
                <li>Share your account credentials with others</li>
                <li>Redistribute or resell signal data</li>
                <li>Attempt to reverse-engineer our algorithms</li>
                <li>Use automated tools to scrape or access the Service</li>
                <li>Use the Service for any illegal purpose</li>
            </ul>
            
            <h2>7. Intellectual Property</h2>
            <p>All content, algorithms, designs, and trademarks are the exclusive property of ELUXRAJ. You may not copy, modify, or distribute any part of the Service without written permission.</p>
            
            <h2>8. Limitation of Liability</h2>
            <p>TO THE MAXIMUM EXTENT PERMITTED BY LAW, ELUXRAJ SHALL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, INCLUDING BUT NOT LIMITED TO LOSS OF PROFITS, DATA, OR TRADING LOSSES, ARISING FROM YOUR USE OF THE SERVICE.</p>
            
            <h2>9. Indemnification</h2>
            <p>You agree to indemnify and hold harmless ELUXRAJ and its officers, directors, employees, and agents from any claims, damages, or expenses arising from your use of the Service or violation of these Terms.</p>
            
            <h2>10. Changes to Terms</h2>
            <p>We reserve the right to modify these Terms at any time. Continued use of the Service after changes constitutes acceptance of the new Terms.</p>
            
            <h2>11. Governing Law</h2>
            <p>These Terms shall be governed by the laws of the State of Delaware, United States, without regard to conflict of law principles.</p>
            
            <h2>12. Contact</h2>
            <p>For questions about these Terms, contact us at: <a href="mailto:legal@eluxraj.ai">legal@eluxraj.ai</a></p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@router.get("/privacy", response_class=HTMLResponse)
async def privacy_policy():
    """Privacy Policy"""
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Privacy Policy - ELUXRAJ</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0a0a0f; color: #ccc; line-height: 1.8; }
            .container { max-width: 800px; margin: 0 auto; padding: 40px 20px; }
            h1 { color: #fff; font-size: 32px; margin-bottom: 10px; background: linear-gradient(135deg, #7c3aed, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            h2 { color: #fff; font-size: 20px; margin: 30px 0 15px; }
            h3 { color: #fff; font-size: 16px; margin: 20px 0 10px; }
            p, li { margin-bottom: 15px; }
            ul { padding-left: 20px; }
            .updated { color: #888; font-size: 14px; margin-bottom: 30px; }
            a { color: #7c3aed; }
            .highlight { background: rgba(124, 58, 237, 0.1); border: 1px solid rgba(124, 58, 237, 0.3); padding: 20px; border-radius: 8px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Privacy Policy</h1>
            <p class="updated">Last Updated: """ + datetime.utcnow().strftime("%B %d, %Y") + """</p>
            
            <p>ELUXRAJ ("we", "our", "us") is committed to protecting your privacy. This policy explains how we collect, use, and safeguard your information.</p>
            
            <h2>1. Information We Collect</h2>
            
            <h3>1.1 Account Information</h3>
            <ul>
                <li>Email address</li>
                <li>Name (optional)</li>
                <li>Password (encrypted)</li>
                <li>Subscription status and payment information</li>
            </ul>
            
            <h3>1.2 Usage Data</h3>
            <ul>
                <li>Signals viewed and interactions</li>
                <li>Feature usage patterns</li>
                <li>Device and browser information</li>
                <li>IP address and approximate location</li>
            </ul>
            
            <h3>1.3 Communications</h3>
            <ul>
                <li>Support requests and feedback</li>
                <li>Email alert preferences</li>
            </ul>
            
            <div class="highlight">
                <h3>🤖 AI & Data Usage Disclosure</h3>
                <p><strong>Our AI models are trained on publicly available market data only.</strong> We do NOT use your personal information, trading history, or account data to train our AI models.</p>
                <p>The ORACLE engine uses:</p>
                <ul>
                    <li>Public price data from CoinGecko API</li>
                    <li>Public market sentiment from Alternative.me Fear & Greed Index</li>
                    <li>Publicly available on-chain metrics</li>
                    <li>Historical market patterns from public datasets</li>
                </ul>
                <p>Your personal data is NEVER used for model training or shared with third parties for AI development.</p>
            </div>
            
            <h2>2. How We Use Your Information</h2>
            <ul>
                <li>Provide and improve our services</li>
                <li>Send signal alerts and notifications you've opted into</li>
                <li>Process payments and manage subscriptions</li>
                <li>Respond to support requests</li>
                <li>Analyze aggregate usage to improve features</li>
                <li>Detect and prevent fraud or abuse</li>
            </ul>
            
            <h2>3. Information Sharing</h2>
            <p>We do NOT sell your personal information. We may share data with:</p>
            <ul>
                <li><strong>Payment processors:</strong> Stripe (for subscription payments)</li>
                <li><strong>Email providers:</strong> SendGrid (for alerts and communications)</li>
                <li><strong>Hosting providers:</strong> Railway (for infrastructure)</li>
                <li><strong>Legal requirements:</strong> When required by law or to protect our rights</li>
            </ul>
            
            <h2>4. Data Security</h2>
            <ul>
                <li>Passwords are encrypted using industry-standard bcrypt hashing</li>
                <li>All data transmitted via HTTPS/TLS encryption</li>
                <li>Database access restricted and monitored</li>
                <li>Regular security audits and updates</li>
            </ul>
            
            <h2>5. Data Retention</h2>
            <ul>
                <li>Account data: Retained while account is active</li>
                <li>Signal history: Retained indefinitely for transparency and auditability</li>
                <li>Usage logs: Retained for 90 days</li>
                <li>Deleted accounts: Data removed within 30 days (except legal obligations)</li>
            </ul>
            
            <h2>6. Your Rights</h2>
            <p>You have the right to:</p>
            <ul>
                <li>Access your personal data</li>
                <li>Correct inaccurate information</li>
                <li>Delete your account and associated data</li>
                <li>Export your data in a portable format</li>
                <li>Opt out of marketing communications</li>
                <li>Withdraw consent for data processing</li>
            </ul>
            
            <h2>7. Cookies & Tracking</h2>
            <p>We use minimal, essential cookies for:</p>
            <ul>
                <li>Authentication and session management</li>
                <li>Security and fraud prevention</li>
            </ul>
            <p>We do NOT use third-party tracking or advertising cookies.</p>
            
            <h2>8. Children's Privacy</h2>
            <p>ELUXRAJ is not intended for users under 18 years of age. We do not knowingly collect information from minors.</p>
            
            <h2>9. International Users</h2>
            <p>Data is processed in the United States. By using our Service, you consent to data transfer to the US. We comply with GDPR requirements for EU users.</p>
            
            <h2>10. Changes to This Policy</h2>
            <p>We may update this policy periodically. We will notify you of material changes via email or in-app notification.</p>
            
            <h2>11. Contact Us</h2>
            <p>For privacy-related inquiries:<br>
            Email: <a href="mailto:privacy@eluxraj.ai">privacy@eluxraj.ai</a></p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@router.get("/disclaimer", response_class=HTMLResponse)
async def disclaimer():
    """Investment Disclaimer"""
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Investment Disclaimer - ELUXRAJ</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0a0a0f; color: #ccc; line-height: 1.8; }
            .container { max-width: 800px; margin: 0 auto; padding: 40px 20px; }
            h1 { color: #fff; font-size: 32px; margin-bottom: 10px; background: linear-gradient(135deg, #7c3aed, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            h2 { color: #fff; font-size: 20px; margin: 30px 0 15px; }
            p, li { margin-bottom: 15px; }
            ul { padding-left: 20px; }
            .updated { color: #888; font-size: 14px; margin-bottom: 30px; }
            .warning { background: rgba(239, 68, 68, 0.15); border: 2px solid rgba(239, 68, 68, 0.5); padding: 30px; border-radius: 12px; margin: 30px 0; }
            .warning h2 { color: #ef4444; margin-top: 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Investment Disclaimer</h1>
            <p class="updated">Last Updated: """ + datetime.utcnow().strftime("%B %d, %Y") + """</p>
            
            <div class="warning">
                <h2>⚠️ IMPORTANT: READ BEFORE USING ELUXRAJ</h2>
                <p><strong>ELUXRAJ is NOT a registered investment advisor, broker-dealer, or financial planner.</strong> The signals, analysis, and information provided are for educational and informational purposes ONLY.</p>
            </div>
            
            <h2>No Investment Advice</h2>
            <p>Nothing on ELUXRAJ constitutes professional financial advice, legal advice, or tax advice. The content is not tailored to your specific financial situation, investment goals, or risk tolerance.</p>
            
            <h2>Trading Risks</h2>
            <p>Trading cryptocurrencies and securities involves substantial risks, including:</p>
            <ul>
                <li><strong>Loss of Capital:</strong> You may lose some or ALL of your invested money</li>
                <li><strong>Volatility:</strong> Cryptocurrency prices can swing 10-50% in a single day</li>
                <li><strong>Liquidity Risk:</strong> You may not be able to sell when you want</li>
                <li><strong>Regulatory Risk:</strong> Laws governing crypto may change</li>
                <li><strong>Technical Risk:</strong> Exchanges may be hacked or fail</li>
                <li><strong>Market Manipulation:</strong> Crypto markets may be manipulated by large players</li>
            </ul>
            
            <h2>AI Limitations</h2>
            <p>Our AI-powered ORACLE system has inherent limitations:</p>
            <ul>
                <li>AI predictions are probabilistic, NOT guaranteed</li>
                <li>Past performance does NOT predict future results</li>
                <li>Models may fail in unprecedented market conditions</li>
                <li>Data sources may contain errors or delays</li>
                <li>Market dynamics change over time, reducing model accuracy</li>
            </ul>
            
            <h2>Your Responsibility</h2>
            <p>By using ELUXRAJ, you acknowledge:</p>
            <ul>
                <li>You are solely responsible for your investment decisions</li>
                <li>You should do your own research before trading</li>
                <li>You should only invest money you can afford to lose</li>
                <li>You should consult a licensed financial advisor for personalized advice</li>
                <li>You understand and accept all risks involved in trading</li>
            </ul>
            
            <h2>No Guarantees</h2>
            <p>ELUXRAJ makes NO guarantees regarding:</p>
            <ul>
                <li>Accuracy of signals or predictions</li>
                <li>Profitability of any trades</li>
                <li>Completeness of market analysis</li>
                <li>Suitability for your investment needs</li>
            </ul>
            
            <h2>Limitation of Liability</h2>
            <p>ELUXRAJ, its owners, employees, and affiliates shall NOT be liable for any losses, damages, or costs arising from:</p>
            <ul>
                <li>Reliance on any signal or information provided</li>
                <li>Trading decisions made based on our content</li>
                <li>Technical failures or data inaccuracies</li>
                <li>Third-party actions or market conditions</li>
            </ul>
            
            <h2>Regulatory Notice</h2>
            <p>ELUXRAJ is not registered with the SEC, CFTC, FINRA, or any other regulatory body. We do not provide regulated financial services. Users in certain jurisdictions may be prohibited from using our service.</p>
            
            <h2>Contact</h2>
            <p>Questions? Contact: <a href="mailto:legal@eluxraj.ai" style="color:#7c3aed;">legal@eluxraj.ai</a></p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@router.get("/methodology", response_class=HTMLResponse)
async def methodology():
    """Methodology & Performance Disclosures"""
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Methodology & Performance - ELUXRAJ</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0a0a0f; color: #ccc; line-height: 1.8; }
            .container { max-width: 800px; margin: 0 auto; padding: 40px 20px; }
            h1 { color: #fff; font-size: 32px; margin-bottom: 10px; background: linear-gradient(135deg, #7c3aed, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            h2 { color: #fff; font-size: 20px; margin: 30px 0 15px; }
            h3 { color: #fff; font-size: 16px; margin: 20px 0 10px; }
            p, li { margin-bottom: 15px; }
            ul, ol { padding-left: 20px; }
            .updated { color: #888; font-size: 14px; margin-bottom: 30px; }
            a { color: #7c3aed; }
            .card { background: #12121a; border: 1px solid #333; padding: 24px; border-radius: 12px; margin: 20px 0; }
            .card h3 { margin-top: 0; }
            .factor { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #333; }
            .factor:last-child { border-bottom: none; }
            .badge { padding: 4px 12px; border-radius: 20px; font-size: 12px; }
            .badge.green { background: rgba(34, 197, 94, 0.2); color: #22c55e; }
            .badge.yellow { background: rgba(245, 158, 11, 0.2); color: #f59e0b; }
            code { background: #1a1a2e; padding: 2px 8px; border-radius: 4px; font-family: monospace; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Methodology & Performance Disclosures</h1>
            <p class="updated">Last Updated: """ + datetime.utcnow().strftime("%B %d, %Y") + """</p>
            
            <p>At ELUXRAJ, we believe in full transparency. This document explains exactly how our AI generates signals and how we measure performance.</p>
            
            <h2>🧠 ORACLE Engine Overview</h2>
            <p>The ORACLE (Optimized Real-time Algorithmic Crypto/Liquid-asset Engine) is our proprietary AI system that generates trading signals by analyzing multiple data sources and factors.</p>
            
            <div class="card">
                <h3>Current Version: oracle-v1.0.0</h3>
                <p>Supported Assets: BTC, ETH, SOL, BNB, XRP, ADA, DOGE, AVAX, DOT, MATIC, LINK, UNI</p>
                <p>Update Frequency: Hourly automatic scans + on-demand analysis</p>
            </div>
            
            <h2>📊 Data Sources</h2>
            <p>Our signals are generated using publicly available data from:</p>
            
            <div class="card">
                <div class="factor"><span><strong>CoinGecko API</strong></span><span class="badge green">Primary</span></div>
                <p style="color:#888;font-size:14px;">Real-time price data, market cap, volume, historical prices, ATH/ATL data</p>
                
                <div class="factor"><span><strong>Alternative.me</strong></span><span class="badge green">Primary</span></div>
                <p style="color:#888;font-size:14px;">Fear & Greed Index for market sentiment analysis</p>
                
                <div class="factor"><span><strong>On-Chain Metrics</strong></span><span class="badge yellow">Simulated</span></div>
                <p style="color:#888;font-size:14px;">Whale activity detection (currently using simulated patterns; real on-chain integration coming soon)</p>
            </div>
            
            <h2>⚙️ Signal Generation Factors</h2>
            <p>Each signal is generated by analyzing these weighted factors:</p>
            
            <div class="card">
                <div class="factor"><span>24h Price Momentum</span><span>15%</span></div>
                <div class="factor"><span>7-Day Trend Analysis</span><span>20%</span></div>
                <div class="factor"><span>Volume Flow Analysis</span><span>15%</span></div>
                <div class="factor"><span>Distance from ATH</span><span>10%</span></div>
                <div class="factor"><span>Market Sentiment (Fear/Greed)</span><span>15%</span></div>
                <div class="factor"><span>Volatility Assessment</span><span>10%</span></div>
                <div class="factor"><span>Whale Activity Detection</span><span>15%</span></div>
            </div>
            
            <h2>📈 Oracle Score Calculation</h2>
            <p>The Oracle Score (0-100) is calculated as a weighted average of all factors:</p>
            
            <div class="card">
                <code>Oracle Score = Σ (Factor Score × Factor Weight)</code>
                <br><br>
                <p><strong>Signal Interpretation:</strong></p>
                <ul>
                    <li><strong>Score ≥ 65:</strong> BUY signal - Bullish confluence detected</li>
                    <li><strong>Score 36-64:</strong> HOLD signal - Neutral/mixed indicators</li>
                    <li><strong>Score ≤ 35:</strong> SELL signal - Bearish confluence detected</li>
                </ul>
            </div>
            
            <h2>🎯 Price Target Methodology</h2>
            <p>Entry, target, and stop-loss prices are calculated dynamically based on:</p>
            <ul>
                <li><strong>Entry Price:</strong> Current market price at signal generation</li>
                <li><strong>Target Price:</strong> 5-12% above entry (scaled by Oracle Score)</li>
                <li><strong>Stop Loss:</strong> 3-5% below entry (inversely scaled by Oracle Score)</li>
                <li><strong>Risk/Reward Ratio:</strong> Always calculated and displayed</li>
            </ul>
            
            <h2>📋 Signal Audit Trail</h2>
            <p>Every signal is permanently logged with:</p>
            <ul>
                <li>Unique signal ID and timestamp</li>
                <li>All input data at time of generation</li>
                <li>Complete factor breakdown</li>
                <li>Model version used</li>
                <li>Outcome tracking (hit target, hit stop, expired)</li>
            </ul>
            <p>View historical signals and outcomes: <a href="/api/v1/transparency/signals">/api/v1/transparency/signals</a></p>
            
            <h2>📊 Performance Tracking</h2>
            <p>We track and publish the following metrics:</p>
            <ul>
                <li><strong>Win Rate:</strong> % of signals that hit target before stop-loss</li>
                <li><strong>Average Return:</strong> Mean P&L across all completed signals</li>
                <li><strong>Risk-Adjusted Return:</strong> Sharpe-like ratio of returns</li>
                <li><strong>Signal Accuracy by Asset:</strong> Per-asset breakdown</li>
                <li><strong>Score Calibration:</strong> Correlation between score and outcome</li>
            </ul>
            <p>View live performance: <a href="/api/v1/transparency/performance">/api/v1/transparency/performance</a></p>
            
            <h2>⚠️ Limitations & Caveats</h2>
            <ul>
                <li>Whale activity is currently simulated pending on-chain integration</li>
                <li>Signals assume sufficient liquidity for execution</li>
                <li>Slippage and fees are NOT factored into targets</li>
                <li>Performance metrics include ALL signals, not cherry-picked results</li>
                <li>Past performance does NOT guarantee future results</li>
                <li>Model accuracy may degrade in unprecedented market conditions</li>
            </ul>
            
            <h2>🔄 Model Updates</h2>
            <p>We continuously improve the ORACLE engine. All updates are logged:</p>
            <ul>
                <li>v1.0.0 (Current): Initial release with 7-factor analysis</li>
            </ul>
            <p>Major model changes will be announced and documented here.</p>
            
            <h2>📞 Questions?</h2>
            <p>For methodology questions: <a href="mailto:research@eluxraj.ai">research@eluxraj.ai</a></p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)
