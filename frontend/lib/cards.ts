import cardsJson from '@/data/cards.json'

/** A collectible card in the catalogue. */
export interface CardItem {
  id: string
  name: string
  description: string | null
  /** Price in cents. */
  price: number
  rarity: string
  category: string
  stock: number
  imageUrl: string | null
  active: boolean
}

export const CATALOGUE: CardItem[] = cardsJson as CardItem[]

/** The cards a buyer can still order. */
export function availableCards(): CardItem[] {
  return CATALOGUE.filter((card) => card.active && card.stock > 0)
}

/**
 * Look a card up by id.
 *
 * The checkout route resolves the cards again on the server, so a buyer cannot
 * send an unknown id and have it priced by the browser.
 */
export function findCard(id: string | null | undefined): CardItem | null {
  if (!id) return null
  return CATALOGUE.find((card) => card.id === id) ?? null
}

/** Format a price for display. */
export function formatPrice(cents: number, currency = 'USD'): string {
  if (cents === 0) return 'ฟรี'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    maximumFractionDigits: 2,
  }).format(cents / 100)
}
