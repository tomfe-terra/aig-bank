export interface PaymentFormData {
  pan: string;
  exp_month: number;
  exp_year: number;
  cvv: string;
  to_account_number: string;
  amount_cents: number;
  meta?: Record<string, any> | null;
}

export interface CardPaymentCreate {
  pan: string;
  exp_month: number;
  exp_year: number;
  cvv: string;
  to_account_number: string;
  amount_cents: number;
  meta?: Record<string, any> | null;
}

export enum TransactionType {
  TRANSFER_OUT = "TRANSFER_OUT",
  TRANSFER_IN = "TRANSFER_IN",
  CARD_PAYMENT = "CARD_PAYMENT",
  LOAN_DISBURSEMENT = "LOAN_DISBURSEMENT",
}

export interface RelatedAccountInfo {
  account_number: string;
  username: string;
}

export interface TransactionRead {
  id: string | null;
  account_id: string | null;
  type: TransactionType;
  amount_cents: number;
  amount_dollars: number;
  related_account_id?: RelatedAccountInfo | null;
  idempotency_key: string;
  meta?: Record<string, any> | null;
  created_at: string;
}

export interface ApiErrorResponse {
  error: string;
  details: string;
  request_id: string;
}

export interface PaymentPageParams {
  account: string;
  amount: string;
  metadata?: string;
  redirect: string;
}

export interface PaymentResult {
  success: boolean;
  transaction?: TransactionRead;
  error?: string;
  redirectUrl?: string;
}

