import * as React from "react";

import { cn } from "@/lib/utils";

export type TableProps = React.ComponentProps<"table"> & { containerClassName?: string };
export type TableHeaderProps = React.ComponentProps<"thead">;
export type TableBodyProps = React.ComponentProps<"tbody">;
export type TableFooterProps = React.ComponentProps<"tfoot">;
export type TableRowProps = React.ComponentProps<"tr">;
export type TableHeadProps = React.ComponentProps<"th">;
export type TableCellProps = React.ComponentProps<"td">;
export type TableCaptionProps = React.ComponentProps<"caption">;

function Table({ className, containerClassName, ...props }: TableProps) {
  return (
    <div data-slot="table-container" className={cn("relative w-full overflow-x-auto rounded-lg border bg-card", containerClassName)}>
      <table data-slot="table" className={cn("w-full caption-bottom text-sm", className)} {...props} />
    </div>
  );
}
function TableHeader({ className, ...props }: TableHeaderProps) {
  return <thead data-slot="table-header" className={cn("bg-muted/60 [&_tr]:border-b", className)} {...props} />;
}
function TableBody({ className, ...props }: TableBodyProps) {
  return <tbody data-slot="table-body" className={cn("[&_tr:last-child]:border-0", className)} {...props} />;
}
function TableFooter({ className, ...props }: TableFooterProps) {
  return <tfoot data-slot="table-footer" className={cn("border-t bg-muted/50 font-medium", className)} {...props} />;
}
function TableRow({ className, ...props }: TableRowProps) {
  return <tr data-slot="table-row" className={cn("border-b transition-colors hover:bg-muted/40", className)} {...props} />;
}
function TableHead({ className, ...props }: TableHeadProps) {
  return <th data-slot="table-head" className={cn("h-11 px-4 text-left align-middle font-mono text-xs font-semibold uppercase tracking-wider text-muted-foreground", className)} {...props} />;
}
function TableCell({ className, ...props }: TableCellProps) {
  return <td data-slot="table-cell" className={cn("p-4 align-middle", className)} {...props} />;
}
function TableCaption({ className, ...props }: TableCaptionProps) {
  return <caption data-slot="table-caption" className={cn("mt-4 text-sm text-muted-foreground", className)} {...props} />;
}

export { Table, TableBody, TableCaption, TableCell, TableFooter, TableHead, TableHeader, TableRow };
