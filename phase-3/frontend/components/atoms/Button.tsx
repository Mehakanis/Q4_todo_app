import { type LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface ButtonProps {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  icon?: LucideIcon;
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void;
  className?: string;
  type?: 'button' | 'submit' | 'reset';
}

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  icon: Icon,
  onClick,
  className,
  type = 'button',
}: ButtonProps) {
  const baseStyles =
    'inline-flex items-center justify-center rounded-lg font-medium transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';

  const variantStyles = {
    primary:
      'glass-card bg-primary/20 hover:bg-primary/30 text-primary border-primary/30 hover:scale-105 focus:ring-primary',
    secondary:
      'glass-card bg-muted/20 hover:bg-muted/30 text-foreground border-border/50 hover:scale-105 focus:ring-muted',
    ghost:
      'bg-transparent hover:bg-primary/10 text-primary border-transparent hover:border-primary/20 hover:scale-105 focus:ring-primary',
  };

  const sizeStyles = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };

  return (
    <button
      type={type}
      className={cn(
        baseStyles,
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
      disabled={disabled || loading}
      onClick={onClick}
    >
      {loading ? (
        <span className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
      ) : Icon ? (
        <Icon className="mr-2 h-4 w-4" />
      ) : null}
      {children}
    </button>
  );
}

