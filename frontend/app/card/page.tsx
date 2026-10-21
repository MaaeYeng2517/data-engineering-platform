import cards from "@/data/cards.json";
import { BuyButton } from "@/components/buy-button";

export const dynamic = "force-dynamic";

export default function CardsPage() {
  return (
    <main className="p-8">
      <h1 className="text-2xl font-bold mb-4">Cards</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {cards.map((c: any) => (
          <div key={c.id} className="border rounded p-4">
            <h2 className="font-semibold">{c.name}</h2>
            <p className="text-sm text-gray-500">{c.description}</p>
            <p className="mt-2 font-bold">${(c.price / 100).toFixed(2)}</p>
            <p className="text-xs">Stock: {c.stock} · {c.rarity}</p>
            <BuyButton cardId={c.id} />
          </div>
        ))}
      </div>
    </main>
  );
}
