import "@testing-library/jest-dom/vitest";

// Mock next/navigation
const mockPush = vi.fn();
const mockReplace = vi.fn();
const mockPathname = "/dashboard";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: mockReplace, back: vi.fn() }),
  usePathname: () => mockPathname,
}));

// Mock next/link as a plain anchor
vi.mock("next/link", () => ({
  default: ({ children, href, ...props }: { children: React.ReactNode; href: string; [k: string]: unknown }) => {
    // eslint-disable-next-line @next/next/no-html-link-for-pages
    return <a href={href} {...props}>{children}</a>;
  },
}));

// Expose mocks for tests
export { mockPush, mockReplace };
