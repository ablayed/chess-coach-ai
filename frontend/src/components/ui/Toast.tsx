"use client";

import clsx from "clsx";

interface ToastProps {
  message: string;
  type?: "info" | "success" | "error";
}

const toneClasses: Record<NonNullable<ToastProps["type"]>, string> = {
  info: "border-cyan-500/40 bg-cyan-500/20 text-cyan-200",
  success: "border-green-500/40 bg-green-500/20 text-green-200",
  error: "border-red-500/40 bg-red-500/20 text-red-200",
};

export function Toast({ message, type = "info" }: ToastProps) {
  return (
    <div className={clsx("rounded-md border px-3 py-2 text-sm", toneClasses[type])} role="status">
      {message}
    </div>
  );
}
