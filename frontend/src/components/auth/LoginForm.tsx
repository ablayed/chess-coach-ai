"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { useAuthStore } from "@/stores/useAuthStore";

export function LoginForm() {
  const router = useRouter();
  const login = useAuthStore((state) => state.login);
  const isLoading = useAuthStore((state) => state.isLoading);
  const storeError = useAuthStore((state) => state.error);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setLocalError(null);

    if (!email || !password) {
      setLocalError("Email and password are required.");
      return;
    }

    try {
      await login(email, password);
      router.push("/");
    } catch {
      // Error state handled by store.
    }
  };

  return (
    <Card className="w-full max-w-md space-y-4">
      <h1 className="text-xl font-semibold text-gray-100">Sign in</h1>
      <form onSubmit={handleSubmit} className="space-y-3">
        <Input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          required
        />
        <Input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
        />

        {(localError || storeError) && <p className="text-sm text-red-400">{localError ?? storeError}</p>}

        <Button type="submit" fullWidth disabled={isLoading}>
          {isLoading ? "Signing in..." : "Sign in"}
        </Button>
      </form>
      <p className="text-sm text-gray-400">
        No account?{" "}
        <Link href="/auth/register" className="text-cyan-300 hover:text-cyan-200">
          Create one
        </Link>
      </p>
    </Card>
  );
}
