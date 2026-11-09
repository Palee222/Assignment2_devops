import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/utils";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "outline" | "ghost" | "subtle" | "danger";
  size?: "default" | "sm" | "icon";
  children: ReactNode;
};

const variants = {
  primary: "bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm",
  outline: "border border-border bg-card text-foreground hover:bg-muted",
  ghost: "text-muted-foreground hover:bg-muted hover:text-foreground",
  subtle: "bg-secondary text-secondary-foreground hover:bg-secondary/70",
  danger: "bg-danger text-primary-foreground hover:bg-danger/90",
};
const sizes = {
  default: "h-10 px-4 gap-2 text-sm",
  sm: "h-8 px-3 gap-1.5 text-xs",
  icon: "h-9 w-9 justify-center",
};

export function AppButton({ variant = "primary", size = "default", className, children, ...props }: Props) {
  return <button className={cn("inline-flex shrink-0 items-center justify-center rounded-md font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-45", variants[variant], sizes[size], className)} {...props}>{children}</button>;
}
