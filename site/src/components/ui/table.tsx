import * as React from "react";

import { cn } from "@/lib/utils";

export type TableProps = React.ComponentProps<"table"> & {
  containerClassName?: string;
};
export type TableHeaderProps = React.ComponentProps<"thead">;
export type TableBodyProps = React.ComponentProps<"tbody">;
export type TableFooterProps = React.ComponentProps<"tfoot">;
export type TableRowProps = React.ComponentProps<"tr">;
export type TableHeadProps = React.ComponentProps<"th">;
export type TableCellProps = React.ComponentProps<"td">;
export type TableCaptionProps = React.ComponentProps<"caption">;

function Table({ className, containerClassName, ...props }: TableProps) {
  return (
    <div data-slot="table-container" className={cn("table-wrapper", containerClassName)}>
      <table data-slot="table" className={cn("table", className)} {...props} />
    </div>
  );
}

function TableHeader({ className, ...props }: TableHeaderProps) {
  return <thead data-slot="table-header" className={cn("table-header", className)} {...props} />;
}

function TableBody({ className, ...props }: TableBodyProps) {
  return <tbody data-slot="table-body" className={cn("table-body", className)} {...props} />;
}

function TableFooter({ className, ...props }: TableFooterProps) {
  return <tfoot data-slot="table-footer" className={cn("table-footer", className)} {...props} />;
}

function TableRow({ className, ...props }: TableRowProps) {
  return <tr data-slot="table-row" className={cn("table-row", className)} {...props} />;
}

function TableHead({ className, ...props }: TableHeadProps) {
  return <th data-slot="table-head" className={cn("table-head", className)} {...props} />;
}

function TableCell({ className, ...props }: TableCellProps) {
  return <td data-slot="table-cell" className={cn("table-cell", className)} {...props} />;
}

function TableCaption({ className, ...props }: TableCaptionProps) {
  return <caption data-slot="table-caption" className={cn("table-caption", className)} {...props} />;
}

export { Table, TableBody, TableCaption, TableCell, TableFooter, TableHead, TableHeader, TableRow };
