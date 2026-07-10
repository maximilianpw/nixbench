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
  return <article data-slot="card" className={cn("card", className)} {...props} />;
}

function CardHeader({ className, ...props }: CardHeaderProps) {
  return <div data-slot="card-header" className={cn("card-header", className)} {...props} />;
}

function CardTitle({ className, ...props }: CardTitleProps) {
  return <h3 data-slot="card-title" className={cn("card-title", className)} {...props} />;
}

function CardDescription({ className, ...props }: CardDescriptionProps) {
  return <p data-slot="card-description" className={cn("card-description", className)} {...props} />;
}

function CardAction({ className, ...props }: CardActionProps) {
  return <div data-slot="card-action" className={cn("card-action", className)} {...props} />;
}

function CardContent({ className, ...props }: CardContentProps) {
  return <div data-slot="card-content" className={cn("card-content", className)} {...props} />;
}

function CardFooter({ className, ...props }: CardFooterProps) {
  return <div data-slot="card-footer" className={cn("card-footer", className)} {...props} />;
}

export { Card, CardAction, CardContent, CardDescription, CardFooter, CardHeader, CardTitle };
