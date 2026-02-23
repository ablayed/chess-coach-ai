"use client";

import clsx from "clsx";
import { forwardRef, InputHTMLAttributes } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(({ className, error, ...props }, ref) => {
  return (
    <div className="w-full">
      <input
        ref={ref}
        className={clsx(
          "w-full rounded-md border bg-gray-950 px-3 py-2 text-sm text-gray-100 outline-none transition",
          error
            ? "border-red-500 focus:border-red-400 focus:ring-2 focus:ring-red-500/20"
            : "border-gray-700 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20",
          className,
        )}
        {...props}
      />
      {error ? <p className="mt-1 text-xs text-red-400">{error}</p> : null}
    </div>
  );
});

Input.displayName = "Input";
