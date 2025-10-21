'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

interface NavLinkProps {
    href: string;
    children: React.ReactNode;
}

export default function NavLink({ href, children }: NavLinkProps) {
    const pathname = usePathname();
    const isActive = pathname === href || (href !== '/' && pathname.startsWith(href));

    return (
        <Link
            href={href}
            className={`
                relative px-4 py-2 text-sm font-semibold rounded-lg transition-all duration-300 group
                ${isActive
                    ? 'text-primary-700 dark:text-primary-400 bg-primary-50 dark:bg-primary-900/20 shadow-sm'
                    : 'text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-gray-100 dark:hover:bg-gray-800/50'
                }
            `}
        >
            <span className="relative z-10">{children}</span>
            {isActive && (
                <div className="absolute inset-0 bg-gradient-to-r from-primary-500/10 to-purple-500/10 rounded-lg"></div>
            )}
            <div className="absolute inset-0 bg-gradient-to-r from-primary-500/5 to-purple-500/5 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
        </Link>
    );
}
