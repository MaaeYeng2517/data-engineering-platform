export default function SuccessPage({ searchParams }: { searchParams: { mock?: string; items?: string } }) {
  return (
    <main className="p-8 text-center">
      <h1 className="text-3xl font-bold text-green-600">Payment Successful!</h1>
      <p className="mt-2">Thank you for your purchase.</p>
      {searchParams.mock && <p className="mt-2 text-sm text-gray-500">Mock mode (no Stripe key configured)</p>}
      <a href="/card" className="mt-4 inline-block underline">Back to cards</a>
    </main>
  );
}
