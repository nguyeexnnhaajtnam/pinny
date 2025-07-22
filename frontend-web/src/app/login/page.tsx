"use client";

import { useForm } from "react-hook-form";
import { useDispatch, useSelector } from "react-redux";
import type { RootState, AppDispatch } from "@/store/store";
import { loginRequest } from "../../store/authSlice";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Button from "../../components/Button";
import Input from "../../components/Input";
import Link from "next/link";
import { GoogleOutlined, FacebookFilled, AppleFilled } from '@ant-design/icons';

type LoginPayload = { email: string; password: string };

interface LoginForm {
  email: string;
  password: string;
}

export default function LoginPage() {
  const dispatch = useDispatch<AppDispatch>();
  const router = useRouter();
  const { loading, error, token } = useSelector((state: RootState) => state.auth);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>();

  useEffect(() => {
    if (token) {
      router.push("/");
    }
  }, [token, router]);

  const onSubmit = (data: LoginForm) => {
    dispatch(loginRequest(data as LoginPayload));
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="w-full max-w-md bg-white rounded-xl shadow-lg p-8">
        <h2 className="text-2xl font-bold mb-6 text-center">Sign in to Pinny</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Input
            id="email"
            label="Email"
            type="email"
            autoComplete="email"
            error={errors.email?.message}
            {...register("email", {
              required: "Please enter your email",
              pattern: {
                value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                message: "Invalid email address",
              },
            })}
          />
          <Input
            id="password"
            label="Password"
            type="password"
            autoComplete="current-password"
            error={errors.password?.message}
            {...register("password", {
              required: "Please enter your password",
            })}
          />
          {error && <div className="text-red-600 text-sm text-center">{error}</div>}
          <Button type="submit" isLoading={loading}>
            Sign In
          </Button>
        </form>
        <div className="my-6 flex items-center justify-center">
          <span className="text-gray-400 text-xs">or continue with</span>
        </div>
        <div className="flex flex-col gap-3">
          <Button
            type="button"
            className="bg-white text-gray-800 border border-gray-300 hover:bg-gray-100 flex items-center justify-center gap-2"
            onClick={() => alert('Google login not implemented yet')}
            isLoading={false}
          >
            <GoogleOutlined style={{ fontSize: 20 }} />
            Continue with Google
          </Button>
          <Button
            type="button"
            className="bg-[#1877F2] text-white hover:bg-[#145db2] flex items-center justify-center gap-2"
            onClick={() => alert('Facebook login not implemented yet')}
            isLoading={false}
          >
            <FacebookFilled style={{ fontSize: 20 }} />
            Continue with Facebook
          </Button>
          <Button
            type="button"
            className="bg-black text-white hover:bg-gray-800 flex items-center justify-center gap-2"
            onClick={() => alert('Apple login not implemented yet')}
            isLoading={false}
          >
            <AppleFilled style={{ fontSize: 20 }} />
            Continue with Apple
          </Button>
        </div>
        <div className="mt-4 text-center text-sm">
          Don&apos;t have an account?{' '}
          <Link href="/auth/register" className="text-blue-600 hover:underline">Register</Link>
        </div>
      </div>
    </div>
  );
}
