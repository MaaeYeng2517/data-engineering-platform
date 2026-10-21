import { NextResponse } from "next/server";

export async function POST(req: Request) {
  const { items } = await req.json();
  return NextResponse.json({ url: `/orders/success?items=${items.map((i: any) => i.cardId).join(",")}` });
}
