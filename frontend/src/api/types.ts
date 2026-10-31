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
