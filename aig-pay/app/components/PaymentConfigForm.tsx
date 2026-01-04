'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { LOGO_PATH } from '../constants';

interface PaymentConfigFormProps {
  initialAccount?: string;
  initialAmount?: string;
  initialRedirect?: string;
}

export default function PaymentConfigForm({
  initialAccount = '',
  initialAmount = '',
  initialRedirect = '',
}: PaymentConfigFormProps) {
  const router = useRouter();
  const [account, setAccount] = useState(initialAccount);
  const [amount, setAmount] = useState(initialAmount);
  const [redirect, setRedirect] = useState(initialRedirect);
  const [error, setError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!account.trim()) {
      setError('Account number is required');
      return;
    }

    if (redirect.trim()) {
      try {
        new URL(redirect);
      } catch {
        setError('Redirect URL must be a valid URL');
        return;
      }
    }

    if (amount.trim()) {
      const amountNum = parseInt(amount);
      if (isNaN(amountNum) || amountNum < 0) {
        setError('Amount must be a valid positive number');
        return;
      }
    }

    const params = new URLSearchParams();
    params.set('account', account);
    if (redirect.trim()) {
      params.set('redirect', redirect);
    }
    if (amount.trim()) {
      params.set('amount', amount);
    }

    router.push(`/?${params.toString()}`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center p-4">
      <div className="w-full max-w-lg mx-auto">
        <div className="bg-white rounded-2xl shadow-xl p-8 md:p-10">
          <div className="mb-8 text-center">
            <div className="w-24 h-24 mx-auto mb-6">
              <img
                src={LOGO_PATH}
                alt="Logo"
                className="w-full h-full object-contain"
              />
            </div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Payment Configuration
            </h1>
            <p className="text-gray-600">
              Enter payment details to continue
            </p>
          </div>

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

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Account Number */}
            <div>
              <label
                htmlFor="account"
                className="block text-sm font-semibold text-gray-700 mb-2"
              >
                Account Number <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                id="account"
                value={account}
                onChange={(e) => setAccount(e.target.value)}
                placeholder="Enter destination account number"
                required
                className="w-full px-4 py-3 text-gray-900 placeholder-gray-400 border-2 border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
              />
            </div>

            {/* Redirect URL */}
            <div>
              <label
                htmlFor="redirect"
                className="block text-sm font-semibold text-gray-700 mb-2"
              >
                Redirect URL <span className="text-gray-400">(optional)</span>
              </label>
              <input
                type="url"
                id="redirect"
                value={redirect}
                onChange={(e) => setRedirect(e.target.value)}
                placeholder="https://example.com/success"
                className="w-full px-4 py-3 text-gray-900 placeholder-gray-400 border-2 border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
              />
              <p className="mt-1 text-xs text-gray-500">
                URL to redirect to after successful payment (5 second delay)
              </p>
            </div>

            {/* Amount (Optional) */}
            <div>
              <label
                htmlFor="amount"
                className="block text-sm font-semibold text-gray-700 mb-2"
              >
                Amount (in cents) <span className="text-gray-400">(optional)</span>
              </label>
              <input
                type="number"
                id="amount"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="50000 (for $500.00)"
                min="0"
                step="1"
                className="w-full px-4 py-3 text-gray-900 placeholder-gray-400 border-2 border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
              />
              <p className="mt-1 text-xs text-gray-500">
                Pre-fill amount in cents (e.g., 50000 = $500.00)
              </p>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              className="w-full mt-6 bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-4 px-6 rounded-xl font-semibold text-lg hover:from-blue-700 hover:to-indigo-700 focus:outline-none focus:ring-4 focus:ring-blue-300 transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 active:translate-y-0"
            >
              Continue to Payment
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-gray-200">
            <div className="text-center text-xs text-gray-500">
              <p className="mb-2">You can also access the payment page directly via URL:</p>
              <code className="block bg-gray-50 px-3 py-2 rounded text-xs break-all">
                /?account=ACCOUNT&redirect=URL&amount=CENTS
              </code>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

