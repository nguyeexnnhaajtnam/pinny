"use client";

import React from "react";

interface FormProps extends React.FormHTMLAttributes<HTMLFormElement> {
  children: React.ReactNode;
  className?: string;
}

export default function Form({ onSubmit, children, className = "", ...rest }: FormProps) {
  return (
    <form onSubmit={onSubmit} className={`space-y-4 ${className}`} {...rest}>
      {children}
    </form>
  );
} 