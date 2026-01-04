'use client';

import { useState, useRef } from 'react';
import { LOGO_PATH } from '../constants';

interface CreditCardFormProps {
  accountNumber: string;
  amountCents: number;
  metadata?: string;
  redirectUrl?: string;
  apiEndpoint?: string;
}

export default function CreditCardForm({
  accountNumber,
  amountCents,
  metadata,
  redirectUrl,
  apiEndpoint,
}: CreditCardFormProps) {
  const [cardNumber, setCardNumber] = useState('');
  const [expMonth, setExpMonth] = useState('');
  const [expYear, setExpYear] = useState('');
  const [cvv, setCvv] = useState('');
  const [amount, setAmount] = useState((amountCents / 100).toFixed(2));
  const [error, setError] = useState('');
  const [isPending, setIsPending] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [redirectCountdown, setRedirectCountdown] = useState<number | null>(null);
  const formRef = useRef<HTMLFormElement>(null);

  const validateCardNumber = (number: string): boolean => {
    const digits = number.replace(/\s/g, '');
    if (!/^\d+$/.test(digits)) return false;
    if (digits.length < 13 || digits.length > 19) return false;

    let sum = 0;
    let isEven = false;

    for (let i = digits.length - 1; i >= 0; i--) {
      let digit = parseInt(digits[i]);

      if (isEven) {
        digit *= 2;
        if (digit > 9) {
          digit -= 9;
        }
      }

      sum += digit;
      isEven = !isEven;
    }

    return sum % 10 === 0;
  };

  const formatCardNumber = (value: string): string => {
    const cleaned = value.replace(/\s/g, '');
    const groups = cleaned.match(/.{1,4}/g);
    return groups ? groups.join(' ') : cleaned;
  };

  const handleCardNumberChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\s/g, '');
    if (value.length <= 19 && /^\d*$/.test(value)) {
      setCardNumber(formatCardNumber(value));
    }
  };

  const handleCvvChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    if (value.length <= 4 && /^\d*$/.test(value)) {
      setCvv(value);
    }
  };

  const handleAmountChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    if (/^\d*\.?\d{0,2}$/.test(value)) {
      setAmount(value);
    }
  };

  const isExpiryValid = (): boolean => {
    if (!expMonth || !expYear) return false;

    const now = new Date();
    const currentYear = now.getFullYear();
    const currentMonth = now.getMonth() + 1;

    const month = parseInt(expMonth);
    const year = parseInt(expYear);

    if (year < currentYear) return false;
    if (year === currentYear && month < currentMonth) return false;

    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!validateCardNumber(cardNumber)) {
      setError('Invalid card number');
      return;
    }

    if (!isExpiryValid()) {
      setError('Card has expired or expiry date is invalid');
      return;
    }

    if (cvv.length < 3 || cvv.length > 4) {
      setError('Invalid CVV');
      return;
    }

    const amountValue = parseFloat(amount);
    if (isNaN(amountValue) || amountValue <= 0) {
      setError('Invalid amount');
      return;
    }

    let meta: Record<string, unknown> | null = null;
    if (metadata) {
      try {
        meta = JSON.parse(metadata);
      } catch (e) {
        meta = { raw: metadata };
      }
    }

    const payload = {
      pan: cardNumber.replace(/\s/g, ''), // Remove spaces from card number
      exp_month: parseInt(expMonth),
      exp_year: parseInt(expYear),
      cvv,
      to_account_number: accountNumber,
      amount_cents: Math.round(amountValue * 100),
      meta,
    };

    setIsPending(true);

    try {
      if (!apiEndpoint) {
        setError('API endpoint not configured');
        setIsPending(false);
        return;
      }

      const response = await fetch(
        `${apiEndpoint}/api/v1/payments/credit-card`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        setError(errorData.details || errorData.error || 'Payment failed');
        setIsPending(false);
        return;
      }

      setIsPending(false);
      setIsSuccess(true);

      if (redirectUrl) {
        setRedirectCountdown(5);
        const countdownInterval = setInterval(() => {
          setRedirectCountdown((prev) => {
            if (prev === null || prev <= 1) {
              clearInterval(countdownInterval);
              window.location.href = redirectUrl;
              return null;
            }
            return prev - 1;
          });
        }, 1000);
      }
    } catch (error) {
      console.error('Payment processing error:', error);
      setError(
        error instanceof Error
          ? error.message
          : 'An unexpected error occurred'
      );
      setIsPending(false);
    }
  };

  const monthOptions = Array.from({ length: 12 }, (_, i) => {
    const month = i + 1;
    return (
      <option key={month} value={month}>
        {month.toString().padStart(2, '0')}
      </option>
    );
  });

  const currentYear = new Date().getFullYear();
  const yearOptions = Array.from({ length: 11 }, (_, i) => {
    const year = currentYear + i;
    return (
      <option key={year} value={year}>
        {year}
      </option>
    );
  });

  if (isSuccess) {
    return (
      <>
        <div className="text-center py-8">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg
              className="w-8 h-8 text-green-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Payment Successful!
          </h2>
          <p className="text-gray-600 mb-4">
            Your payment has been processed successfully.
          </p>
          {redirectCountdown !== null && (
            <p className="text-sm text-gray-500">
              Redirecting in {redirectCountdown} second{redirectCountdown !== 1 ? 's' : ''}...
            </p>
          )}
        </div>
      </>
    );
  }

  return (
    <>
      {/* Payment info header */}
      <div className="mb-6 pb-6 border-b border-gray-200">
        <p className="text-center text-sm text-gray-500">
          Payment to account
        </p>
        <p className="text-center text-lg font-semibold text-gray-900">
          {accountNumber}
        </p>
      </div>

      {/* Error message */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 rounded-md">
          <div className="flex">
            <svg
              className="w-5 h-5 text-red-500 mr-2"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
            <p className="text-sm font-medium text-red-700">{error}</p>
          </div>
        </div>
      )}

        <form ref={formRef} onSubmit={handleSubmit} className="space-y-5">
          {/* Amount */}
          <div>
            <label
              htmlFor="amount"
              className="block text-sm font-semibold text-gray-700 mb-2"
            >
              Amount
            </label>
            <div className="relative">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 text-lg font-medium">
                $
              </span>
              <input
                type="text"
                id="amount"
                value={amount}
                onChange={handleAmountChange}
                placeholder="0.00"
                required
                disabled={isPending}
                className="w-full pl-9 pr-4 py-3 text-lg text-gray-900 placeholder-gray-400 border-2 border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:cursor-not-allowed transition-all"
              />
            </div>
          </div>

          {/* Card Number */}
          <div>
            <label
              htmlFor="pan"
              className="block text-sm font-semibold text-gray-700 mb-2"
            >
              Card Number
            </label>
            <div className="relative">
              <input
                type="text"
                id="pan"
                name="pan"
                value={cardNumber}
                onChange={handleCardNumberChange}
                placeholder="1234 5678 9012 3456"
                required
                disabled={isPending}
                className="w-full px-4 py-3 text-gray-900 placeholder-gray-400 border-2 border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:cursor-not-allowed transition-all font-mono"
              />
              <div className="absolute right-4 top-1/2 -translate-y-1/2">
                <svg
                  className="w-8 h-8 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"
                  />
                </svg>
              </div>
            </div>
          </div>

          {/* Expiry Date and CVV */}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label
                htmlFor="exp_month"
                className="block text-sm font-semibold text-gray-700 mb-2"
              >
                Month
              </label>
              <select
                id="exp_month"
                name="exp_month"
                value={expMonth}
                onChange={(e) => setExpMonth(e.target.value)}
                required
                disabled={isPending}
                className="w-full px-4 py-3 text-gray-900 border-2 border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:cursor-not-allowed transition-all appearance-none bg-white"
              >
                <option value="">MM</option>
                {monthOptions}
              </select>
            </div>

            <div>
              <label
                htmlFor="exp_year"
                className="block text-sm font-semibold text-gray-700 mb-2"
              >
                Year
              </label>
              <select
                id="exp_year"
                name="exp_year"
                value={expYear}
                onChange={(e) => setExpYear(e.target.value)}
                required
                disabled={isPending}
                className="w-full px-4 py-3 text-gray-900 border-2 border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:cursor-not-allowed transition-all appearance-none bg-white"
              >
                <option value="">YYYY</option>
                {yearOptions}
              </select>
            </div>

            <div>
              <label
                htmlFor="cvv"
                className="block text-sm font-semibold text-gray-700 mb-2"
              >
                CVV
              </label>
              <input
                type="text"
                id="cvv"
                name="cvv"
                value={cvv}
                onChange={handleCvvChange}
                placeholder="123"
                required
                disabled={isPending}
                className="w-full px-4 py-3 text-gray-900 placeholder-gray-400 border-2 border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:cursor-not-allowed transition-all text-center font-mono"
              />
            </div>
          </div>

          {/* Hidden fields */}
          <input type="hidden" name="to_account_number" value={accountNumber} />
          <input type="hidden" name="amount_cents" value={Math.round(parseFloat(amount) * 100)} />
          <input type="hidden" name="meta" value={metadata || ''} />
          <input type="hidden" name="redirect_url" value={redirectUrl} />

          {/* Submit button */}
          <button
            type="submit"
            disabled={isPending}
            className="w-full mt-6 bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-4 px-6 rounded-xl font-semibold text-lg hover:from-blue-700 hover:to-indigo-700 focus:outline-none focus:ring-4 focus:ring-blue-300 disabled:from-gray-400 disabled:to-gray-400 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 active:translate-y-0"
          >
            {isPending ? (
              <span className="flex items-center justify-center">
                <svg
                  className="animate-spin -ml-1 mr-3 h-6 w-6 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                Processing Payment...
              </span>
            ) : (
              <span className="flex items-center justify-center">
                <svg
                  className="w-5 h-5 mr-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                  />
                </svg>
                Complete Secure Payment
              </span>
            )}
          </button>
        </form>

      {/* Security notice */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <div className="flex items-center justify-center text-sm text-gray-500">
          <svg
            className="w-5 h-5 text-green-500 mr-2"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z"
              clipRule="evenodd"
            />
          </svg>
          <span>Secure SSL encrypted payment</span>
        </div>
      </div>
    </>
  );
}

