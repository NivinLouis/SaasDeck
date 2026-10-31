import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { Plan } from "../api/types";

function ArrowUpRight() {
  return <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3 13 13 3M5 3h8v8" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" /></svg>;
}

function BrandLockup() {
  return <div className="landing-brand" aria-label="Brightloop"><span className="landing-brand__mark"><i /><i /><i /></span><span>brightloop</span></div>;
}

function DashboardPreview() {
  return (
    <div className="dashboard-preview" aria-label="Brightloop dashboard preview">
      <div className="dashboard-preview__sidebar">
        <BrandLockup />
        <div className="preview-workspace"><span />Northstar project</div>
        <div className="preview-nav"><b>Overview</b><span>Workflows</span><span>Migration</span><span>Training</span><span>Support</span></div>
        <div className="preview-user"><span>MS</span><div><strong>Maria Singh</strong><small>Project owner</small></div></div>
      </div>
      <div className="dashboard-preview__main">
        <div className="preview-topbar"><div><span>Implementation workspace</span><strong>Northstar go-live plan</strong></div><button>View project <ArrowUpRight /></button></div>
        <div className="preview-metrics">
          <div><span>Workflows configured</span><strong>12</strong><small><i /> 4 complete <em>this week</em></small></div>
          <div><span>Migration readiness</span><strong>86%</strong><small><i /> On track <em>for go-live</em></small></div>
          <div><span>Open decisions</span><strong>3</strong><small className="warning"><i /> Needs input <em>this week</em></small></div>
        </div>
        <div className="preview-panels">
          <section className="revenue-panel"><div className="panel-title"><div><span>Implementation progress</span><strong>Project milestones</strong></div><small>12 week plan⌄</small></div><div className="chart"><div className="chart-grid" /><svg viewBox="0 0 510 155" preserveAspectRatio="none" aria-hidden="true"><defs><linearGradient id="area" x1="0" x2="0" y1="0" y2="1"><stop stopColor="#6958fd" stopOpacity=".32"/><stop offset="1" stopColor="#6958fd" stopOpacity="0"/></linearGradient></defs><path d="M0 122 C30 106 36 113 63 102 S93 90 117 93 S154 114 181 92 S216 64 242 83 S280 97 307 68 S341 82 367 57 S398 49 428 39 S466 52 510 13 V155 H0Z" fill="url(#area)"/><path d="M0 122 C30 106 36 113 63 102 S93 90 117 93 S154 114 181 92 S216 64 242 83 S280 97 307 68 S341 82 367 57 S398 49 428 39 S466 52 510 13" fill="none" stroke="#6958fd" strokeWidth="3"/></svg><div className="chart-labels"><span>Discover</span><span>Design</span><span>Build</span><span>Test</span><span>Train</span><span>Go live</span></div></div></section>
          <section className="activity-panel"><div className="panel-title"><div><span>Latest activity</span><strong>Project updates</strong></div><small>View all</small></div><div className="activity-row"><span className="avatar avatar--orange">W</span><div><strong>Workflow review</strong><small>Finance approved</small></div><b>Done</b></div><div className="activity-row"><span className="avatar avatar--lavender">D</span><div><strong>Data migration</strong><small>Import validation</small></div><b>86%</b></div><div className="activity-row"><span className="avatar avatar--pink">T</span><div><strong>Team training</strong><small>Session scheduled</small></div><b>Oct 30</b></div></section>
        </div>
      </div>
    </div>
  );
}

const showcaseFeatures: Record<string, string[]> = {
  "starter-daily": ["Core CRM workspace", "Flexible daily billing", "Guided setup checklist"],
  "growth-weekly": ["Team workflows", "Automation starter pack", "Priority implementation support"],
  "pro-monthly": ["Accounting, CRM & inventory", "Automated backups", "Net 15 payment terms"],
  "enterprise-yearly": ["Dedicated cloud environment", "Custom integrations", "24×7 mission-critical support"],
};

function formatMoney(value: string, currency: string) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency, maximumFractionDigits: 0 }).format(Number(value));
}

function ProductShowcase() {
  const { data, isLoading } = useQuery({ queryKey: ["public-plan-showcase"], queryFn: () => api.get<Plan[]>("/showcase/plans") });
  const linkedPlans = (data ?? []).filter((plan): plan is Plan & { product: number; product_detail: NonNullable<Plan["product_detail"]> } => Boolean(plan.product_detail && plan.product !== null));
  const plans = Object.values(linkedPlans.reduce<Record<number, Plan>>((products, plan) => {
    const current = products[plan.product];
    if (!current || Number(plan.price) < Number(current.price)) products[plan.product] = plan;
    return products;
  }, {}));
  return <section className="software-showcase" id="software"><div className="landing-container"><div className="software-showcase__head"><div><p className="section-kicker">SOFTWARE FOR THE WORK AHEAD</p><h2>Choose a platform your<br /><em>team will love using.</em></h2></div><p>Start with the service that fits today. Add capability as your operation grows, with a clear quote before anything begins.</p></div>{isLoading ? <div className="showcase-loading">Loading available software…</div> : plans.length ? <div className="product-showcase-grid">{plans.map((plan, index) => <article className={`product-showcase-card ${index === 2 ? "product-showcase-card--featured" : ""}`} key={plan.id}><div className="product-showcase-card__top"><span>{plan.product_detail?.product_type.replaceAll("_", " ") ?? "software"}</span>{plan.trial_period_days ? <b>{plan.trial_period_days}-day trial</b> : null}</div><h3>{plan.name}</h3><p>{plan.description || plan.product_detail?.description || "A complete Brightloop software service for your team."}</p><div className="product-showcase-card__price"><strong>{formatMoney(plan.price, plan.currency)}</strong><small>per {plan.interval_count === 1 ? plan.billing_interval : `${plan.interval_count} ${plan.billing_interval}s`}</small></div><ul>{(showcaseFeatures[plan.code] ?? ["Secure cloud delivery", "Guided onboarding", "Flexible subscription management"]).map((feature) => <li key={feature}><i>✓</i>{feature}</li>)}</ul><Link to="/register" className="product-showcase-card__action">Request a quote <ArrowUpRight /></Link></article>)}</div> : <div className="showcase-loading">Our software catalogue is being refreshed. Sign in to see available plans.</div>}<p className="software-showcase__note">Already a Brightloop customer? <Link to="/login">Sign in to choose a plan and request your quotation.</Link></p></div></section>;
}

export function LandingPage() {
  return <main className="landing-page">
    <section className="hero" id="top">
      <div className="mesh" aria-hidden="true"><i /><i /><i /><i /></div>
      <nav className="landing-nav landing-container" aria-label="Main navigation"><BrandLockup /><div className="landing-nav__links"><a href="#software">Software</a><a href="#services">Services</a><a href="#approach">Our approach</a></div><div className="landing-nav__actions"><Link to="/login" className="text-link">Client sign in</Link><a href="#software" className="pill-button">Explore software <ArrowUpRight /></a></div></nav>
      <div className="landing-container hero__content"><p className="section-kicker"><span /> Brightloop software implementation</p><h1>Software that works<br /><em>the way you do.</em></h1><p className="hero__lede">Brightloop designs, implements, and supports the systems your team depends on - from subscription billing to customer operations and reporting.</p><div className="hero__actions"><a href="#software" className="pill-button pill-button--large">Explore our software <ArrowUpRight /></a><a className="play-link" href="#approach"><span>▶</span> See our approach</a></div><p className="hero__note">Discovery-led <i /> Built around your workflow</p></div>
      <div className="hero__product landing-container"><DashboardPreview /></div>
    </section>

    <section className="proof landing-container" aria-label="Customer promise"><p>A practical implementation partner from first workflow to confident go-live</p><div><span>SUBSCRIPTION BUSINESSES</span><span>FINANCE TEAMS</span><span>OPERATIONS</span><span>SALES TEAMS</span><span>SERVICE COMPANIES</span></div></section>

    <ProductShowcase />

    <section className="feature-intro" id="services"><div className="landing-container"><p className="section-kicker">IMPLEMENTATION THAT FITS</p><div className="section-heading"><h2>More than software.<br />A system your team <em>can use.</em></h2><p>We turn your operating needs into a clear, connected implementation - with the workflows, data, and team readiness to make it stick.</p></div><div className="feature-grid"><article className="feature-card feature-card--wide"><span className="feature-number">01</span><div><p>Workflow-led design</p><h3>Start with how<br />your business works.</h3><a href="#approach">See our approach <ArrowUpRight /></a></div><div className="subscription-visual"><div className="sub-line"><span className="logo-dot">N</span><div><strong>Northstar implementation</strong><small>Subscription operations</small></div><b>On track</b></div><div className="sub-timeline"><i /><span>Discover</span><i /><span>Configure</span><i className="is-active"/><strong>Go live</strong></div><div className="sub-foot"><span>Current phase</span><strong>Configuration</strong><b>Week 6 of 12</b></div></div></article><article className="feature-card feature-card--dark"><span className="feature-number">02</span><div><p>Connected operations</p><h3>Bring the work<br />into one place.</h3><a href="#approach">Explore delivery <ArrowUpRight /></a></div><div className="invoice-mini"><div><span>IMPLEMENTATION SCOPE</span><strong>Operations platform</strong><small>Designed around the customer journey</small></div><p><span>Subscription plans</span><b>Ready</b></p><p><span>Billing &amp; payments</span><b>Ready</b></p><footer><span>Launch readiness</span><strong>86%</strong></footer></div></article></div></div></section>

    <section className="metrics-band" id="approach"><div className="landing-container"><div><p className="section-kicker">A CLEAR PATH TO GO-LIVE</p><h2>Less uncertainty.<br />More useful software.</h2><p className="metrics-copy">You get a shared plan, visible progress, and an implementation team that stays close to the detail - so adoption is built in, not bolted on.</p><a className="arrow-link" href="#contact">Talk through your project <ArrowUpRight /></a></div><div className="metrics-panel"><div className="metrics-panel__head"><span>Implementation plan</span><b>Week 6 of 12</b></div><div className="donut-row"><div className="donut"><span><strong>86%</strong><small>ready</small></span></div><div><span>Go-live readiness</span><strong>On track</strong><small>Configuration and training underway</small></div></div><div className="metrics-bars"><p><span>Discovery completed</span><b>100%</b></p><i><em /></i><p><span>Configuration</span><b>86%</b></p><i className="metrics-bars__upcoming"><em /></i><p><span>Training scheduled</span><b>60%</b></p><i className="metrics-bars__overdue"><em /></i></div></div></div></section>

    <section className="teams landing-container" id="teams"><p className="section-kicker">A COMPLETE IMPLEMENTATION PARTNERSHIP</p><div className="section-heading"><h2>From first workflow<br />to a team that’s <em>ready.</em></h2><p>We bring the right structure at every stage, so your technology earns trust from the people expected to use it every day.</p></div><div className="team-grid"><article><span className="team-icon team-icon--purple">01</span><h3>Discover &amp; design</h3><p>Map the workflows, exceptions, and priorities that matter before configuration begins.</p><a href="#contact">Plan the foundation <ArrowUpRight /></a></article><article><span className="team-icon team-icon--orange">02</span><h3>Implement &amp; migrate</h3><p>Configure the system, move the data, and connect the pieces that keep operations flowing.</p><a href="#contact">See the delivery plan <ArrowUpRight /></a></article><article><span className="team-icon team-icon--pink">03</span><h3>Train &amp; support</h3><p>Prepare your team for day one and stay close as the new way of working takes hold.</p><a href="#contact">Meet the team <ArrowUpRight /></a></article></div></section>

    <section className="closing-cta" id="contact"><div className="closing-cta__mesh" aria-hidden="true" /><div className="landing-container"><p className="section-kicker">START WITH A CONVERSATION</p><h2>Make your next<br />system <em>count.</em></h2><p>Tell us what needs to work better. We’ll help you build a practical path from today’s process to a confident go-live.</p><Link to="/register" className="pill-button pill-button--large">Start your implementation <ArrowUpRight /></Link></div></section>
    <footer className="landing-footer landing-container"><BrandLockup /><p>© 2026 Brightloop Software. Implementation that fits your business.</p><div><a href="#top">Privacy</a><a href="#top">Terms</a><a href="#contact">Contact</a></div></footer>
  </main>;
}
