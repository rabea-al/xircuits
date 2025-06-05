

export class LinkSplitManager {
  private static hoveredLinkId: string | null = null;
  static getHoveredLinkId(): string | null {
    return this.hoveredLinkId;}
  
  static detectLinkUnderPointer(clientX: number, clientY: number): string | null {
  const els = document.elementsFromPoint(clientX, clientY) as HTMLElement[];
  const gEl = els.find(el => el.dataset && el.dataset.linkid);
  return gEl?.dataset?.linkid ?? null;
}


  
static setHover(linkId: string | null): void {
  if (linkId === this.hoveredLinkId) return;
  this.clearHover();                            
  if (linkId) {
    const g = document.querySelector(
      `g[data-linkid="${linkId}"]`
    ) as SVGGElement | null;

    g?.classList.add('hover');

  }
  this.hoveredLinkId = linkId;
}

static clearHover(): void {
  if (!this.hoveredLinkId) return;

  const g = document.querySelector(
    `g[data-linkid="${this.hoveredLinkId}"]`
  ) as SVGGElement | null;

  g?.classList.remove('hover');


  this.hoveredLinkId = null;
}
}