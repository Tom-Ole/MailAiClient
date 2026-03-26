import { redirect } from '@sveltejs/kit';
import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async ({ fetch, url }) => {
  const isAuthPage = url.pathname === '/auth';

  const res = await fetch('/api/auth/me');

  if (res.ok) {
    if (isAuthPage) redirect(303, '/');
    const user = await res.json();
    return { user };
  } else {
    if (!isAuthPage) redirect(303, '/auth');
    return { user: null };
  }
};