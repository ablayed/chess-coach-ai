"use client";

import { PropsWithChildren, useEffect } from "react";

import { useAuthStore } from "@/stores/useAuthStore";

export function Providers({ children }: PropsWithChildren) {
  const initialize = useAuthStore((state) => state.initialize);

  useEffect(() => {
    initialize();
  }, [initialize]);

  return children;
}
