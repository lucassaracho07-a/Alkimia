-- Endurecimiento opcional de RLS (NO ejecutado todavía).
--
-- Motivo: el POS se valida con un login local, así que cualquier persona con
-- la clave anónima embebida en el .exe podría escribir en la base. Este script
-- revoca a "anon" y "authenticated" las operaciones que la app NO usa, según
-- la auditoría de app/db/:
--
--   products      -> insert, update, delete   (el inventario los necesita)
--   sales         -> solo via rpc("register_sale"), que es security definer
--   sale_items    -> solo dentro de register_sale
--   cash_cuts     -> solo insert (cuts.py)
--   settings      -> upsert (store_settings.py), nunca delete
--   app_releases  -> solo select (services/updates.py)
--
-- Ejecutar en Supabase > SQL Editor. Todas las sentencias son idempotentes y
-- reversibles con "grant" si algo falla.

-- Histórico financiero: solo se escribe desde register_sale (security definer).
revoke insert, update, delete on public.sales from anon, authenticated;
revoke insert, update, delete on public.sale_items from anon, authenticated;

-- Cortes de caja: solo se crean, no se editan ni se borran.
revoke update, delete on public.cash_cuts from anon, authenticated;

-- Ajustes del negocio: upsert, nunca se borran.
revoke delete on public.settings from anon, authenticated;

-- Catálogo de versiones: solo lectura.
revoke insert, update, delete on public.app_releases from anon, authenticated;

-- Verificación: después de aplicarlo, esto debe dar 0 permisos para
-- delete sobre sales/sale_items:
-- select grantee, table_name, privilege_type
--   from information_schema.role_table_grants
--  where table_schema = 'public'
--    and table_name in ('sales', 'sale_items', 'cash_cuts')
--    and grantee in ('anon', 'authenticated')
--  order by table_name, privilege_type;
