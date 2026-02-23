"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { useAuthStore } from "@/stores/useAuthStore";

export function RegisterForm() {
  const router = useRouter();
  const register = useAuthStore((state) => state.register);
  const isLoading = useAuthStore((state) => state.isLoading);
  const storeError = useAuthStore((state) => state.error);

  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setLocalError(null);

    if (username.length < 3) {
      setLocalError("Username must be at least 3 characters.");
      return;
    }
    if (password.length < 8) {
      setLocalError("Password must be at least 8 characters.");
      return;
    }

    try {
      await register(email, password, username);
      router.push("/");
    } catch {
      // Error state handled by store.
    }
  };

  return (
    <Card className="w-full max-w-md space-y-4">
      <h1 className="text-xl font-semibold text-gray-100">Create account</h1>
      <form onSubmit={handleSubmit} className="space-y-3">
        <Input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          required
        />
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
          {isLoading ? "Creating account..." : "Create account"}
        </Button>
      </form>
      <p className="text-sm text-gray-400">
        Already have an account?{" "}
        <Link href="/auth/login" className="text-cyan-300 hover:text-cyan-200">
          Sign in
        </Link>
      </p>
    </Card>
  );
}
