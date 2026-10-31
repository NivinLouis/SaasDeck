export type UserRole = "admin" | "staff" | "customer";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  date_joined: string;
}

export interface Customer {
  id: number;
  user: number | null;
  name: string;
  company: string;
  email: string;
  phone: string;
  billing_address: string;
  city: string;
  state: string;
  country: string;
  postal_code: string;
  tax_id: string;
  created_at: string;
  updated_at: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface TokenPair {
  access: string;
  refresh: string;
}

export interface ValidationErrorResponse {
  code: "validation_error";
  message: string;
  fields: Record<string, string[]>;
}

export type InvoiceStatus = "DRAFT" | "CONFIRMED" | "PAID" | "CANCELLED";
export type PaymentStatus = "UNPAID" | "PARTIALLY_PAID" | "PAID";

export interface InvoiceLine {
  id: number;
  description: string;
  quantity: number;
  unit_price: string;
  discount_amount: string;
  tax_rate_percent: string;
  tax_amount: string;
  line_total: string;
}

export interface Invoice {
  uuid: string;
  invoice_number: string;
  status: InvoiceStatus;
  payment_status: PaymentStatus;
  issue_date: string;
  due_date: string;
  billing_period_start: string | null;
  billing_period_end: string | null;
  currency: string;
  payment_terms: string;
  notes: string | null;
  customer_snapshot: Record<string, string>;
  subtotal_amount: string;
  discount_amount: string;
  tax_amount: string;
  total_amount: string;
  amount_paid: string;
  amount_due: string;
  is_overdue: boolean;
  pdf_document: string | null;
  lines: InvoiceLine[];
  created_at: string;
  updated_at: string;
}

export type ProductType = "service" | "consumable" | "addon" | "storage";

export interface AppliedTax {
  id: number;
  name: string;
  rate: string;
  is_inclusive: boolean;
}

export interface Product {
  id: number;
  name: string;
  sku: string;
  description: string | null;
  product_type: ProductType;
  sales_price: string;
  is_active: boolean;
  applied_taxes: AppliedTax[];
  created_at: string;
  updated_at: string;
}

export type BillingInterval = "daily" | "weekly" | "monthly" | "yearly";

export interface Plan {
  id: number;
  product: number;
  product_detail: Pick<Product, "id" | "name" | "sku" | "product_type" | "sales_price">;
  name: string;
  code: string;
  description: string | null;
  billing_interval: BillingInterval;
  interval_count: number;
  price: string;
  currency: string;
  minimum_quantity: number;
  payment_term: number | null;
  payment_term_detail: { id: number; name: string; days: number } | null;
  trial_period_days: number;
  auto_close_on_expiry: boolean;
  allow_early_closure: boolean;
  allow_pause: boolean;
  allow_auto_renewal: boolean;
  available_from: string | null;
  available_until: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface QuotationTemplateLine {
  id: number;
  product: number;
  product_name: string;
  variant: number | null;
  variant_value: string | null;
  quantity: number;
  discount_percent: string;
}

export interface QuotationTemplate {
  uuid: string;
  name: string;
  plan: number;
  plan_detail: Pick<Plan, "id" | "name" | "code" | "price" | "currency" | "billing_interval" | "interval_count">;
  validity_days: number;
  terms_and_conditions: string | null;
  is_active: boolean;
  lines: QuotationTemplateLine[];
  created_at: string;
  updated_at: string;
}

export type SubscriptionStatus = "DRAFT" | "QUOTATION" | "CONFIRMED" | "TRIAL" | "ACTIVE" | "PAUSED" | "CANCELLED" | "EXPIRED" | "CLOSED";

export interface Subscription {
  uuid: string;
  subscription_number: string;
  customer: number;
  customer_detail: Pick<Customer, "id" | "name" | "company" | "email">;
  plan: number;
  plan_detail: Pick<Plan, "id" | "name" | "code" | "price" | "currency" | "billing_interval" | "interval_count">;
  applied_discount: string | null;
  template: number | null;
  template_detail: { uuid: string; name: string; validity_days: number } | null;
  quotation_valid_until: string | null;
  lines: Array<{ id: number; product: number; product_name: string; variant: number | null; variant_value: string | null; quantity: number; unit_price: string; discount_percent: string }>;
  audit_events: Array<{ action: string; from_status: string; to_status: string; reason: string; actor_email: string | null; created_at: string }>;
  status: SubscriptionStatus;
  start_date: string | null;
  expiry_date: string | null;
  current_period_start: string | null;
  current_period_end: string | null;
  next_billing_date: string | null;
  payment_terms: string;
  auto_renew: boolean;
  cancellation_reason: string | null;
  closed_at: string | null;
  created_at: string;
  updated_at: string;
}

export type PaymentMethod = "CREDIT_CARD" | "BANK_TRANSFER" | "UPI" | "CASH" | "STRIPE" | "RAZORPAY" | "OTHER";
export type RecordedPaymentStatus = "PENDING" | "COMPLETED" | "FAILED" | "REFUNDED";

export interface Payment {
  uuid: string;
  payment_number: string;
  invoice: number;
  invoice_detail: Pick<Invoice, "uuid" | "invoice_number" | "total_amount" | "amount_paid" | "amount_due" | "currency" | "payment_status">;
  payment_method: PaymentMethod;
  status: RecordedPaymentStatus;
  amount: string;
  currency: string;
  transaction_reference: string | null;
  payment_date: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface Tax {
  id: number;
  name: string;
  rate: string;
  is_inclusive: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProductAttribute {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProductVariant {
  id: number;
  product: number;
  attribute: number;
  value: string;
  price_extra: string;
  final_price: string;
  created_at: string;
  updated_at: string;
}

export interface PaymentTerm {
  id: number;
  name: string;
  days: number;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface BillingRun {
  uuid: string;
  run_date: string;
  status: "STARTED" | "COMPLETED" | "PARTIAL" | "FAILED";
  triggered_by_email: string | null;
  finished_at: string | null;
  subscriptions_considered: number;
  invoices_created: number;
  invoices_existing: number;
  failures: Array<{ subscription?: string; message?: string }>;
  created_at: string;
  updated_at: string;
}

export interface Notification {
  uuid: string;
  title: string;
  body: string;
  category: string;
  read_at: string | null;
  created_at: string;
}

export interface NotificationPreference {
  email_overdue_reminders: boolean;
  in_app_overdue_reminders: boolean;
}

export type DiscountType = "PERCENTAGE" | "FIXED_AMOUNT";
export type DiscountScope = "SUBSCRIPTION" | "PRODUCTS" | "PLANS";

export interface DiscountRule {
  uuid: string;
  code: string;
  name: string;
  description: string | null;
  discount_type: DiscountType;
  value: string;
  scope: DiscountScope;
  minimum_purchase_amount: string;
  minimum_quantity: number;
  valid_from: string;
  valid_until: string | null;
  max_uses: number | null;
  times_used: number;
  is_active: boolean;
  applicable_products: number[];
  applicable_plans: number[];
  created_at: string;
  updated_at: string;
}

export interface DashboardSummary {
  filters?: { start_date: string | null; end_date: string | null };
  subscriptions: { total: number; by_status: Partial<Record<SubscriptionStatus, number>> };
  invoices: { total: number; paid_total: string; outstanding_total: string; overdue_count: number };
  trend?: Array<{ month: string; invoiced_total: string; paid_total: string; invoice_count: number }>;
}
