"use client";

import clsx from "clsx";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useMemo, useState } from "react";

import { Button } from "@/components/ui/Button";
import { useAuthStore } from "@/stores/useAuthStore";

interface NavItem {
  href: string;
  label: string;
  authOnly?: boolean;
  guestOnly?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { href: "/analyze", label: "Analyze" },
  { href: "/review", label: "Review" },
  { href: "/games", label: "Games", authOnly: true },
  { href: "/auth/login", label: "Login", guestOnly: true },
  { href: "/auth/register", label: "Register", guestOnly: true },
];

function isActive(pathname: string, href: string): boolean {
  if (href === "/") {
    return pathname === "/";
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function SiteHeader() {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);

  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);

  const links = useMemo(
    () =>
      NAV_ITEMS.filter((item) => {
        if (item.authOnly && !user) {
          return false;
        }
        if (item.guestOnly && user) {
          return false;
        }
        return true;
      }),
    [user],
  );

  return (
    <header className="sticky top-0 z-50 border-b border-gray-800 bg-gray-950/90 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 md:px-6">
        <Link href="/" className="text-lg font-bold text-cyan-300">
          ChessCoach AI
        </Link>

        <button
          type="button"
          aria-expanded={isOpen}
          aria-label="Toggle navigation"
          onClick={() => setIsOpen((prev) => !prev)}
          className="rounded-md border border-gray-700 px-3 py-2 text-sm text-gray-200 md:hidden"
        >
          Menu
        </button>

        <nav className="hidden items-center gap-2 md:flex">
          {links.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                "rounded-md px-3 py-2 text-sm transition",
                isActive(pathname, item.href)
                  ? "bg-cyan-500/20 text-cyan-200"
                  : "text-gray-300 hover:bg-gray-800 hover:text-cyan-100",
              )}
            >
              {item.label}
            </Link>
          ))}
          {user ? (
            <>
              <span className="mx-1 text-xs text-gray-500">{user.username}</span>
              <Button size="sm" variant="ghost" onClick={logout}>
                Logout
              </Button>
            </>
          ) : null}
        </nav>
      </div>

      {isOpen ? (
        <nav className="space-y-1 border-t border-gray-800 px-4 py-3 md:hidden">
          {links.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setIsOpen(false)}
              className={clsx(
                "block rounded-md px-3 py-2 text-sm transition",
                isActive(pathname, item.href)
                  ? "bg-cyan-500/20 text-cyan-200"
                  : "text-gray-300 hover:bg-gray-800 hover:text-cyan-100",
              )}
            >
              {item.label}
            </Link>
          ))}
          {user ? (
            <button
              type="button"
              onClick={() => {
                logout();
                setIsOpen(false);
              }}
              className="block w-full rounded-md px-3 py-2 text-left text-sm text-gray-300 hover:bg-gray-800 hover:text-cyan-100"
            >
              Logout
            </button>
          ) : null}
        </nav>
      ) : null}
    </header>
  );
}
