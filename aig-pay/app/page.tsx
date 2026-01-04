import CreditCardForm from './components/CreditCardForm';
import PaymentConfigForm from './components/PaymentConfigForm';
import { LOGO_PATH } from './constants';

interface HomePageProps {
  searchParams: Promise<{
    account?: string;
    amount?: string;
    metadata?: string;
    redirect?: string;
  }>;
}

export default async function HomePage({ searchParams }: HomePageProps) {
  const params = await searchParams;
  const { account, amount, metadata, redirect } = params;

  if (!account) {
    return (
      <PaymentConfigForm
        initialAccount={account}
        initialAmount={amount}
        initialRedirect={redirect}
      />
    );
  }

  if (amount) {
    const amountNum = parseInt(amount);
    if (isNaN(amountNum) || amountNum < 0) {
      return (
        <PaymentConfigForm
          initialAccount={account}
          initialAmount=""
          initialRedirect={redirect}
        />
      );
    }
  }

  const amountCents = amount ? parseInt(amount) : 0;

  const apiEndpoint = process.env.API_ENDPOINT || process.env.NEXT_PUBLIC_API_ENDPOINT;

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
              Secure Payment
            </h1>
            <p className="text-gray-600">
              Complete your transaction securely
            </p>
          </div>

          <CreditCardForm
            accountNumber={account!}
            amountCents={amountCents}
            metadata={metadata}
            redirectUrl={redirect}
            apiEndpoint={apiEndpoint}
          />
        </div>
      </div>
    </div>
  );
}
