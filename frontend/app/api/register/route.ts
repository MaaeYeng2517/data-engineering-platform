import { NextResponse } from "next/server";

export async function POST(req: Request) {
  const { email } = await req.json();
  return NextResponse.json({ ok: true, email });
}
