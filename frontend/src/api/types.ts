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
