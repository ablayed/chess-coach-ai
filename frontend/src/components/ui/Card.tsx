import clsx from "clsx";
import { PropsWithChildren } from "react";

interface CardProps extends PropsWithChildren {
  className?: string;
}

export function Card({ className, children }: CardProps) {
  return (
    <div className={clsx("rounded-xl border border-gray-700 bg-gray-800/70 p-4 shadow-card", className)}>
      {children}
    </div>
  );
}
