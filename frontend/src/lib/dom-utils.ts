export function isTextInputFocused(): boolean {
  if (typeof document === "undefined") {
    return false;
  }

  const active = document.activeElement;
  if (!active) {
    return false;
  }

  if (active instanceof HTMLInputElement || active instanceof HTMLTextAreaElement || active instanceof HTMLSelectElement) {
    return true;
  }

  return active instanceof HTMLElement && active.isContentEditable;
}
