"use client";

import React from "react";

interface ErrorMessageProps {
  message?: string;
}

export default function ErrorMessage({ message }: ErrorMessageProps) {
  if (!message) return null;
  return (
    <div className="text-red-600 text-sm text-center my-2">{message}</div>
  );
} 