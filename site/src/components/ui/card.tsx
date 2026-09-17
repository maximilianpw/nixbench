import * as React from "react";

import { cn } from "@/lib/utils";

export type CardProps = React.ComponentProps<"article">;
export type CardHeaderProps = React.ComponentProps<"div">;
export type CardTitleProps = React.ComponentProps<"h3">;
export type CardDescriptionProps = React.ComponentProps<"p">;
export type CardActionProps = React.ComponentProps<"div">;
export type CardContentProps = React.ComponentProps<"div">;
export type CardFooterProps = React.ComponentProps<"div">;

function Card({ className, ...props }: CardProps) {
  return <article data-slot="card" className={cn("flex flex-col gap-6 rounded-lg border bg-card py-6 text-card-foreground", className)} {...props} />;
}
function CardHeader({ className, ...props }: CardHeaderProps) {
  return <div data-slot="card-header" className={cn("grid gap-2 px-6", className)} {...props} />;
}
function CardTitle({ className, ...props }: CardTitleProps) {
  return <h3 data-slot="card-title" className={cn("text-lg font-semibold leading-tight tracking-tight", className)} {...props} />;
}
function CardDescription({ className, ...props }: CardDescriptionProps) {
  return <p data-slot="card-description" className={cn("text-sm leading-6 text-muted-foreground", className)} {...props} />;
}
function CardAction({ className, ...props }: CardActionProps) {
  return <div data-slot="card-action" className={cn("self-start", className)} {...props} />;
}
function CardContent({ className, ...props }: CardContentProps) {
  return <div data-slot="card-content" className={cn("px-6", className)} {...props} />;
}
function CardFooter({ className, ...props }: CardFooterProps) {
  return <div data-slot="card-footer" className={cn("flex items-center px-6", className)} {...props} />;
}

export { Card, CardAction, CardContent, CardDescription, CardFooter, CardHeader, CardTitle };
