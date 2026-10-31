import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { Button, EmptyState, PageHeader, SelectField, TextAreaField, TextField } from "../components/ui";

type FieldType = "text" | "email" | "number" | "date" | "password" | "textarea" | "select";

export interface ModuleField {
  name: string;
  label: string;
  type: FieldType;
  required?: boolean;
  options?: string[];
  wide?: boolean;
}

export interface ModuleDefinition {
  eyebrow: string;
  title: string;
  singular: string;
  description: string;
  columns: string[];
  fields: ModuleField[];
  createPath?: string;
  listPath?: string;
  apiStatus: "API ready" | "API pending";
}

const productFields: ModuleField[] = [
  { name: "name", label: "Product name", type: "text", required: true },
  { name: "sku", label: "SKU", type: "text", required: true },
  { name: "product_type", label: "Product type", type: "select", options: ["Service", "Consumable", "Subscription add-on", "Storage / quota"] },
  { name: "sales_price", label: "Sales price", type: "number", required: true },
  { name: "cost_price", label: "Cost price", type: "number" },
  { name: "description", label: "Notes", type: "textarea", wide: true },
];

// Route configuration is intentionally colocated with its generic page renderers.
// eslint-disable-next-line react-refresh/only-export-components
export const modules = {
  customerEdit: { eyebrow: "Customers", title: "Customer", singular: "customer", description: "Review and update the customer contact and billing details.", columns: [], fields: [{ name: "name", label: "Customer name", type: "text", required: true }, { name: "company", label: "Company", type: "text" }, { name: "email", label: "Email address", type: "email", required: true }, { name: "phone", label: "Phone", type: "text" }, { name: "billing_address", label: "Billing address", type: "textarea", wide: true }, { name: "city", label: "City", type: "text" }, { name: "state", label: "State", type: "text" }, { name: "country", label: "Country", type: "text" }, { name: "postal_code", label: "Postal code", type: "text" }, { name: "tax_id", label: "Tax ID", type: "text" }], listPath: "/customers", apiStatus: "API ready" },
  team: { eyebrow: "Administration", title: "Team members", singular: "team member", description: "Manage the internal people who can access Brightloop operations.", columns: ["Name", "Email", "Role", "Account status"], fields: [{ name: "full_name", label: "Full name", type: "text", required: true }, { name: "email", label: "Email address", type: "email", required: true }, { name: "role", label: "Role", type: "select", options: ["Staff", "Admin"] }, { name: "password", label: "Temporary password", type: "text", required: true }], createPath: "/team/new", listPath: "/team", apiStatus: "API ready" },
  products: { eyebrow: "Catalog", title: "Products", singular: "product", description: "Define the services and add-ons that can be added to subscriptions.", columns: ["Product", "SKU", "Type", "Sales price", "Status"], fields: productFields, createPath: "/products/new", listPath: "/products", apiStatus: "API pending" },
  taxes: { eyebrow: "Catalog", title: "Taxes", singular: "tax", description: "Configure the tax rules used when subscription and invoice totals are calculated.", columns: ["Tax name", "Rate", "Price treatment", "Status"], fields: [{ name: "name", label: "Tax name", type: "text", required: true }, { name: "rate", label: "Rate (%)", type: "number", required: true }, { name: "treatment", label: "Price treatment", type: "select", options: ["Exclusive", "Inclusive"] }], createPath: "/taxes/new", listPath: "/taxes", apiStatus: "API pending" },
  attributes: { eyebrow: "Catalog", title: "Product variants", singular: "variant attribute", description: "Define variant attributes and price adjustments, such as brand or storage tier.", columns: ["Attribute", "Product", "Values", "Price adjustment"], fields: [{ name: "attribute_name", label: "Attribute name", type: "text", required: true }, { name: "product", label: "Product", type: "text", required: true }, { name: "value", label: "Value", type: "text", required: true }, { name: "price_extra", label: "Extra price", type: "number" }], createPath: "/attributes/new", listPath: "/attributes", apiStatus: "API pending" },
  plans: { eyebrow: "Catalog", title: "Plans", singular: "plan", description: "Set recurring pricing, availability, and lifecycle rules for subscriptions.", columns: ["Plan", "Billing interval", "Price", "Minimum quantity", "Status"], fields: [{ name: "name", label: "Plan name", type: "text", required: true }, { name: "code", label: "Plan code", type: "text", required: true }, { name: "billing_interval", label: "Billing interval", type: "select", options: ["Daily", "Weekly", "Monthly", "Yearly"] }, { name: "price", label: "Price", type: "number", required: true }, { name: "minimum_quantity", label: "Minimum quantity", type: "number" }, { name: "available_from", label: "Available from", type: "date" }, { name: "available_until", label: "Available until", type: "date" }], createPath: "/plans/new", listPath: "/plans", apiStatus: "API pending" },
  paymentTerms: { eyebrow: "Catalog", title: "Payment terms", singular: "payment term", description: "Define when invoices become due after they are issued.", columns: ["Name", "Due in days", "Description", "Status"], fields: [{ name: "name", label: "Term name", type: "text", required: true }, { name: "days", label: "Due in days", type: "number", required: true }, { name: "description", label: "Description", type: "textarea", wide: true }], createPath: "/payment-terms/new", listPath: "/payment-terms", apiStatus: "API pending" },
  quotationTemplates: { eyebrow: "Sales", title: "Quotation templates", singular: "quotation template", description: "Prepare reusable offers with standard plans and product lines.", columns: ["Template", "Plan", "Validity", "Status"], fields: [{ name: "name", label: "Template name", type: "text", required: true }, { name: "plan", label: "Plan", type: "text", required: true }, { name: "validity_days", label: "Validity (days)", type: "number", required: true }, { name: "terms", label: "Terms and conditions", type: "textarea", wide: true }], createPath: "/quotation-templates/new", listPath: "/quotation-templates", apiStatus: "API pending" },
  subscriptions: { eyebrow: "Sales", title: "Subscriptions", singular: "subscription", description: "Create and manage the full lifecycle from draft quotation to active service.", columns: ["Subscription", "Customer", "Plan", "Next billing", "Status"], fields: [{ name: "customer", label: "Customer", type: "text", required: true }, { name: "plan", label: "Plan", type: "text", required: true }, { name: "start_date", label: "Start date", type: "date" }, { name: "expiry_date", label: "Expiry date", type: "date" }, { name: "payment_terms", label: "Payment terms", type: "text" }], createPath: "/subscriptions/new", listPath: "/subscriptions", apiStatus: "API pending" },
  discounts: { eyebrow: "Pricing", title: "Discounts", singular: "discount rule", description: "Create time-bound percentage or fixed discounts for selected products, plans, or subscriptions.", columns: ["Code", "Discount", "Scope", "Validity", "Usage"], fields: [{ name: "code", label: "Discount code", type: "text", required: true }, { name: "name", label: "Rule name", type: "text", required: true }, { name: "type", label: "Discount type", type: "select", options: ["Percentage", "Fixed amount"] }, { name: "value", label: "Value", type: "number", required: true }, { name: "valid_from", label: "Starts", type: "date" }, { name: "valid_until", label: "Ends", type: "date" }], createPath: "/discounts/new", listPath: "/discounts", apiStatus: "API pending" },
  payments: { eyebrow: "Billing", title: "Payments", singular: "payment", description: "Record and review payments received against invoices.", columns: ["Payment", "Invoice", "Method", "Amount", "Date", "Status"], fields: [{ name: "invoice", label: "Invoice", type: "text", required: true }, { name: "method", label: "Payment method", type: "select", options: ["Bank transfer", "UPI", "Card", "Cash", "Other"] }, { name: "amount", label: "Amount", type: "number", required: true }, { name: "payment_date", label: "Payment date", type: "date", required: true }, { name: "note", label: "Note", type: "textarea", wide: true }], createPath: "/payments/new", listPath: "/payments", apiStatus: "API pending" },
  billingRuns: { eyebrow: "Billing", title: "Billing runs", singular: "billing run", description: "Review scheduled recurring billing runs and resolve any failures.", columns: ["Run", "Started", "Invoices created", "Failures", "Status"], fields: [], listPath: "/billing-runs", apiStatus: "API pending" },
  reports: { eyebrow: "Insights", title: "Reports", singular: "report", description: "Explore revenue, collections, subscription health, and overdue invoice trends.", columns: ["Report", "Period", "Grouping", "Last updated"], fields: [], listPath: "/reports", apiStatus: "API pending" },
  notifications: { eyebrow: "Operations", title: "Notifications", singular: "notification", description: "Review customer and internal notifications related to subscriptions and billing.", columns: ["Notification", "Recipient", "Channel", "Sent at", "Status"], fields: [], listPath: "/notifications", apiStatus: "API pending" },
  portalSubscriptions: { eyebrow: "Customer portal", title: "My subscriptions", singular: "subscription request", description: "Review your active services and request changes when your plan allows them.", columns: ["Subscription", "Plan", "Next billing", "Expiry", "Status"], fields: [], listPath: "/portal/subscriptions", apiStatus: "API pending" },
  portalSubscriptionDetail: { eyebrow: "Customer portal", title: "Subscription detail", singular: "subscription change", description: "View a subscription and request an allowed pause, resume, renewal, or closure.", columns: [], fields: [], listPath: "/portal/subscriptions", apiStatus: "API pending" },
  security: { eyebrow: "Account", title: "Password and security", singular: "password", description: "Update your password to keep your account protected.", columns: [], fields: [{ name: "current_password", label: "Current password", type: "password", required: true }, { name: "new_password", label: "New password", type: "password", required: true }, { name: "confirm_password", label: "Confirm new password", type: "password", required: true }], listPath: "/settings/security", apiStatus: "API ready" },
} satisfies Record<string, ModuleDefinition>;

export function ModuleListPage({ module }: { module: ModuleDefinition }) {
  return <><PageHeader eyebrow={module.eyebrow} title={module.title} description={module.description} action={module.createPath ? <Link className="button button--primary" to={module.createPath}>Add {module.singular}</Link> : undefined} /><section className="module-status"><span className={module.apiStatus === "API ready" ? "status-badge status-badge--paid" : "status-badge status-badge--draft"}>{module.apiStatus}</span><p>Page structure is ready. No placeholder records are shown.</p></section><section className="data-card module-list"><div className="module-list__head">{module.columns.map((column) => <span key={column}>{column}</span>)}</div><EmptyState title={`No ${module.title.toLowerCase()} to show`} description={module.apiStatus === "API ready" ? "Connect this screen to load records from the available API." : "Records will appear here once the backend API is released and connected."} /></section></>;
}

export function ModuleFormPage({ module, mode = "create" }: { module: ModuleDefinition; mode?: "create" | "edit" }) {
  const [notice, setNotice] = useState<string>();
  const canSave = module.fields.length > 0;
  const actionLabel = mode === "edit" ? "Edit" : "Add";

  function saveDraft(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setNotice(`${module.singular.charAt(0).toUpperCase()}${module.singular.slice(1)} form is ready for API integration.`);
  }

  return <><PageHeader eyebrow={module.eyebrow} title={`${actionLabel} ${module.singular}`} description={module.description} action={module.listPath ? <Link className="button button--secondary" to={module.listPath}>Back to {module.title.toLowerCase()}</Link> : undefined} /><form className="profile-card" onSubmit={saveDraft}><div className="profile-card__section"><h2>{module.singular.charAt(0).toUpperCase()}${module.singular.slice(1)} details</h2>{canSave ? <div className="form-grid">{module.fields.map((field) => field.type === "textarea" ? <TextAreaField key={field.name} label={field.label} name={field.name} required={field.required} rows={3} containerClassName={field.wide ? "field--wide" : undefined} /> : field.type === "select" ? <SelectField key={field.name} label={field.label} name={field.name} options={field.options ?? []} required={field.required} /> : <TextField key={field.name} label={field.label} name={field.name} type={field.type} required={field.required} />)}</div> : <EmptyState title="No manual fields needed" description="This operational page will load its data once the corresponding backend API is connected." />}</div>{notice ? <p className="form-alert form-alert--success" role="status">{notice}</p> : null}{canSave ? <div className="form-actions"><Button type="submit">Save {module.singular}</Button></div> : null}</form></>;
}
