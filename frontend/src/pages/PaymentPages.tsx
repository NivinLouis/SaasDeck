import { useEffect, useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Link, useNavigate, useParams } from "react-router-dom";
import { z } from "zod";
import { api, ApiError } from "../api/client";
import type { Invoice, PaginatedResponse, Payment, PaymentMethod } from "../api/types";
import { useAuth } from "../auth/useAuth";
import { Button, DataTable, EmptyState, ErrorState, LoadingState, PageHeader, StatusBadge, TextAreaField, TextField, type TableColumn } from "../components/ui";

const paymentMethods: Array<{ value: PaymentMethod; label: string }> = [
  { value: "BANK_TRANSFER", label: "Bank transfer" },
  { value: "UPI", label: "UPI" },
  { value: "CREDIT_CARD", label: "Credit / debit card" },
  { value: "CASH", label: "Cash" },
  { value: "STRIPE", label: "Stripe" },
  { value: "RAZORPAY", label: "Razorpay" },
  { value: "OTHER", label: "Other" },
];

function useAccessToken() {
  const { accessToken } = useAuth();
  if (!accessToken) throw new Error("A signed-in session is required.");
  return accessToken;
}

function formatMoney(value: string, currency: string) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency, maximumFractionDigits: 2 }).format(Number(value));
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("en-IN", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" }).format(new Date(value));
}

function paymentMethodLabel(value: PaymentMethod) {
  return paymentMethods.find((method) => method.value === value)?.label ?? value;
}

export function PaymentsPage() {
  const token = useAccessToken();
  const { data, isLoading, isError, error, refetch } = useQuery({ queryKey: ["payments"], queryFn: () => api.get<PaginatedResponse<Payment>>("/payments?page_size=50", token) });
  const columns: TableColumn<Payment>[] = [
    { id: "payment", header: "Payment", cell: (payment) => <Link className="table-link" to={`/payments/${payment.uuid}`}><strong>{payment.payment_number}</strong><small>{payment.transaction_reference || "No external reference"}</small></Link> },
    { id: "invoice", header: "Invoice", cell: (payment) => <Link className="table-link" to={`/invoices/${payment.invoice_detail.uuid}`}>{payment.invoice_detail.invoice_number}</Link> },
    { id: "method", header: "Method", cell: (payment) => paymentMethodLabel(payment.payment_method) },
    { id: "amount", header: "Amount", cell: (payment) => <strong>{formatMoney(payment.amount, payment.currency)}</strong> },
    { id: "date", header: "Received", cell: (payment) => formatDateTime(payment.payment_date) },
    { id: "status", header: "Status", cell: (payment) => <StatusBadge value={payment.status} /> },
  ];
  return <><PageHeader eyebrow="Billing" title="Payments" description="Record and review payments received against confirmed invoices." action={<Link className="button button--primary" to="/payments/new">Record payment</Link>} />{isLoading ? <LoadingState title="Loading payments" description="Retrieving payment records and invoice references." /> : null}{isError ? <ErrorState title="Could not load payments" description={error instanceof ApiError ? error.message : "Please check your connection and try again."} onRetry={() => void refetch()} /> : null}{data ? <section className="data-card"><div className="data-card__summary"><strong>{data.count}</strong><span>payment{data.count === 1 ? "" : "s"}</span></div>{data.results.length ? <DataTable label="Payments" columns={columns} rows={data.results} getRowKey={(payment) => payment.uuid} /> : <EmptyState title="No payments recorded" description="Record a payment against a confirmed invoice once money has been received." action={<Link className="button button--primary" to="/payments/new">Record payment</Link>} />}</section> : null}</>;
}

const paymentFormSchema = z.object({
  invoice: z.string().min(1, "Choose a confirmed invoice."),
  payment_method: z.enum(["CREDIT_CARD", "BANK_TRANSFER", "UPI", "CASH", "STRIPE", "RAZORPAY", "OTHER"]),
  amount: z.string().trim().refine((value) => !Number.isNaN(Number(value)) && Number(value) > 0, "Enter an amount greater than zero."),
  payment_date: z.string().min(1, "Choose the received date and time."),
  transaction_reference: z.string().trim(),
  notes: z.string().trim(),
});

type PaymentFormValues = z.infer<typeof paymentFormSchema>;

function currentLocalDateTime() {
  const date = new Date();
  const offset = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 16);
}

export function PaymentFormPage() {
  const token = useAccessToken();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [notice, setNotice] = useState<string>();
  const invoicesQuery = useQuery({ queryKey: ["invoices", "for-payment"], queryFn: () => api.get<PaginatedResponse<Invoice>>("/invoices?page_size=100&status=CONFIRMED", token) });
  const { register, handleSubmit, watch, setValue, formState: { errors, isSubmitting } } = useForm<PaymentFormValues>({ resolver: zodResolver(paymentFormSchema), defaultValues: { invoice: "", payment_method: "BANK_TRANSFER", amount: "", payment_date: currentLocalDateTime(), transaction_reference: "", notes: "" } });
  const selectedInvoiceId = watch("invoice");
  const selectedInvoice = invoicesQuery.data?.results.find((invoice) => invoice.uuid === selectedInvoiceId);

  useEffect(() => { if (selectedInvoice) setValue("amount", selectedInvoice.amount_due); }, [selectedInvoice, setValue]);

  async function onSubmit(values: PaymentFormValues) {
    setNotice(undefined);
    try {
      const payment = await api.post<Payment>("/payments", { invoice: values.invoice, payment_method: values.payment_method, amount: values.amount, payment_date: new Date(values.payment_date).toISOString(), transaction_reference: values.transaction_reference || "", notes: values.notes || "" }, token);
      await Promise.all([queryClient.invalidateQueries({ queryKey: ["payments"] }), queryClient.invalidateQueries({ queryKey: ["invoices"] })]);
      navigate(`/payments/${payment.uuid}`, { replace: true });
    } catch (submitError) {
      setNotice(submitError instanceof ApiError ? submitError.message : "The payment could not be recorded.");
    }
  }

  if (invoicesQuery.isLoading) return <LoadingState title="Loading payable invoices" description="Retrieving confirmed invoices with an outstanding balance." />;
  if (invoicesQuery.isError) return <ErrorState title="Could not load invoices" description={invoicesQuery.error instanceof ApiError ? invoicesQuery.error.message : "Please check your connection and try again."} onRetry={() => void invoicesQuery.refetch()} />;
  const invoices = (invoicesQuery.data?.results ?? []).filter((invoice) => Number(invoice.amount_due) > 0);
  return <><PageHeader eyebrow="Billing" title="Record payment" description="Apply a received payment to one confirmed invoice." action={<Link className="button button--secondary" to="/payments">Back to payments</Link>} /><form className="profile-card" onSubmit={handleSubmit(onSubmit)} noValidate><div className="profile-card__section"><h2>Payment details</h2>{invoices.length ? <div className="form-grid"><label className="field field--wide"><span className="field__label">Confirmed invoice</span><select className="input select-input" aria-invalid={Boolean(errors.invoice)} {...register("invoice")}><option value="">Choose an invoice</option>{invoices.map((invoice) => <option key={invoice.uuid} value={invoice.uuid}>{invoice.invoice_number} · {formatMoney(invoice.amount_due, invoice.currency)} due</option>)}</select>{errors.invoice ? <span className="field__error">{errors.invoice.message}</span> : null}</label><label className="field"><span className="field__label">Payment method</span><select className="input select-input" {...register("payment_method")}>{paymentMethods.map((method) => <option key={method.value} value={method.value}>{method.label}</option>)}</select></label><TextField label="Amount received" type="number" min="0.01" step="0.01" error={errors.amount?.message} {...register("amount")} /><TextField label="Received at" type="datetime-local" error={errors.payment_date?.message} {...register("payment_date")} /><TextField label="Transaction reference" hint="Optional bank or gateway reference" {...register("transaction_reference")} /><TextAreaField label="Notes" rows={4} containerClassName="field--wide" {...register("notes")} /></div> : <EmptyState title="No invoices are ready for payment" description="Confirm an invoice first, then it will be available to record a payment." action={<Link className="button button--primary" to="/invoices">View invoices</Link>} />}</div>{notice ? <p className="form-alert" role="alert">{notice}</p> : null}{invoices.length ? <div className="form-actions"><Button type="submit" disabled={isSubmitting}>{isSubmitting ? "Recording…" : "Record payment"}</Button></div> : null}</form></>;
}

export function PaymentDetailPage() {
  const token = useAccessToken();
  const { user } = useAuth();
  const { paymentId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [feedback, setFeedback] = useState<string>();
  const { data: payment, isLoading, isError, error, refetch } = useQuery({ queryKey: ["payment", paymentId], enabled: Boolean(paymentId), queryFn: () => api.get<Payment>(`/payments/${paymentId}`, token) });
  const refund = useMutation({
    mutationFn: () => api.post<Payment>(`/payments/${paymentId}/refund`, undefined, token),
    onSuccess: (updated) => { queryClient.setQueryData(["payment", paymentId], updated); void Promise.all([queryClient.invalidateQueries({ queryKey: ["payments"] }), queryClient.invalidateQueries({ queryKey: ["invoices"] })]); setFeedback("Payment refunded and the invoice balance recalculated."); },
    onError: (refundError) => setFeedback(refundError instanceof ApiError ? refundError.message : "The payment could not be refunded."),
  });

  if (isLoading) return <LoadingState title="Loading payment" description="Retrieving the payment record." />;
  if (isError || !payment) return <ErrorState title="Could not load this payment" description={error instanceof ApiError ? error.message : "The payment is unavailable."} onRetry={() => void refetch()} />;
  const canRefund = (user?.role === "admin" || user?.role === "staff") && payment.status === "COMPLETED";
  return <><PageHeader eyebrow="Billing" title={payment.payment_number} description={`${paymentMethodLabel(payment.payment_method)} payment for ${payment.invoice_detail.invoice_number}`} action={<div className="page-actions"><Button type="button" tone="secondary" onClick={() => navigate("/payments")}>Back to payments</Button>{canRefund ? <Button type="button" tone="quiet" disabled={refund.isPending} onClick={() => refund.mutate()}>Refund payment</Button> : null}</div>} />{feedback ? <p className="form-alert" role="status">{feedback}</p> : null}<section className="invoice-overview"><div className="invoice-overview__status"><StatusBadge value={payment.status} /></div><div><span>Amount received</span><strong>{formatMoney(payment.amount, payment.currency)}</strong></div><div><span>Received at</span><strong>{formatDateTime(payment.payment_date)}</strong></div><div><span>Method</span><strong>{paymentMethodLabel(payment.payment_method)}</strong></div></section><section className="profile-card subscription-details"><div className="profile-card__section"><h2>Payment record</h2><dl className="detail-list"><div><dt>Invoice</dt><dd><Link className="table-link" to={`/invoices/${payment.invoice_detail.uuid}`}>{payment.invoice_detail.invoice_number}</Link></dd></div><div><dt>Invoice balance</dt><dd>{formatMoney(payment.invoice_detail.amount_due, payment.currency)}</dd></div><div><dt>Transaction reference</dt><dd>{payment.transaction_reference || "—"}</dd></div><div><dt>Notes</dt><dd>{payment.notes || "—"}</dd></div></dl></div></section></>;
}
