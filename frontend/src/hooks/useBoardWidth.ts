"use client";

import { useEffect, useState } from "react";

export function useBoardWidth(maxWidth = 520) {
  const [width, setWidth] = useState(maxWidth);

  useEffect(() => {
    const update = () => {
      setWidth(Math.max(240, Math.min(window.innerWidth - 32, maxWidth)));
    };

    update();
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, [maxWidth]);

  return width;
}
