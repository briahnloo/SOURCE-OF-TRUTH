'use client';

import { useState, useEffect, useRef } from 'react';
import { usePathname } from 'next/navigation';
import NavLink from './NavLink';

export default function MobileMenu() {
    const [isOpen, setIsOpen] = useState(false);
    const menuRef = useRef<HTMLDivElement>(null);
    const pathname = usePathname();

    // Close menu on route change
    useEffect(() => {
        setIsOpen(false);
    }, [pathname]);

    // Close menu when clicking outside
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        }
        if (isOpen) {
            document.addEventListener('mousedown', handleClickOutside);
            return () => document.removeEventListener('mousedown', handleClickOutside);
        }
    }, [isOpen]);

    // Prevent body scroll when menu is open
    useEffect(() => {
        if (isOpen) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = 'unset';
        }
        return () => {
            document.body.style.overflow = 'unset';
        };
    }, [isOpen]);

    const handleNavClick = () => {
        setIsOpen(false);
    };

    return (
        <div className="md:hidden relative" ref={menuRef}>
            {/* Hamburger Button */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 active:bg-gray-200 dark:active:bg-gray-700 transition-colors touch-manipulation"
                aria-label="Toggle menu"
                aria-expanded={isOpen}
                aria-haspopup="true"
            >
                {/* Hamburger Icon */}
                <div className="w-6 h-6 flex flex-col justify-center space-y-1.5">
                    <span
                        className={`block h-0.5 w-full bg-gray-700 dark:bg-gray-300 transition-all duration-300 ${
                            isOpen ? 'rotate-45 translate-y-2' : ''
                        }`}
                    ></span>
                    <span
                        className={`block h-0.5 w-full bg-gray-700 dark:bg-gray-300 transition-all duration-300 ${
                            isOpen ? 'opacity-0' : ''
                        }`}
                    ></span>
                    <span
                        className={`block h-0.5 w-full bg-gray-700 dark:bg-gray-300 transition-all duration-300 ${
                            isOpen ? '-rotate-45 -translate-y-2' : ''
                        }`}
                    ></span>
                </div>
            </button>

            {/* Dropdown Menu */}
            {isOpen && (
                <div className="absolute top-full left-0 right-0 mt-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl z-50 animate-slide-down">
                    <nav className="flex flex-col py-2 min-w-max">
                        <div onClick={handleNavClick} className="px-2">
                            <NavLink href="/">Confirmed</NavLink>
                        </div>
                        <div onClick={handleNavClick} className="px-2">
                            <NavLink href="/developing">Developing</NavLink>
                        </div>
                        <div onClick={handleNavClick} className="px-2">
                            <NavLink href="/conflicts">Conflicts</NavLink>
                        </div>
                        <div onClick={handleNavClick} className="px-2">
                            <NavLink href="/polarizing">Polarizing</NavLink>
                        </div>
                        <div onClick={handleNavClick} className="px-2">
                            <NavLink href="/flagged">Flagged</NavLink>
                        </div>
                        <div onClick={handleNavClick} className="px-2">
                            <NavLink href="/stats">Stats</NavLink>
                        </div>
                    </nav>
                </div>
            )}
        </div>
    );
}
