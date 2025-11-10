// supabaseClient.js
import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm'

export const supabase = createClient(
  'https://jftrkenddbzdheboymxg.supabase.co',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpmdHJrZW5kZGJ6ZGhlYm95bXhnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjIyNjE0NTYsImV4cCI6MjA3NzgzNzQ1Nn0.55Pppz20H604mFbCZqnxPlQzzmg7TM0zDCmFXvexQHQ'
);
