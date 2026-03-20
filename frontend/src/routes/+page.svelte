<script lang="ts">
  import EmailList from "$lib/EmailList.svelte";

</script>

<div class="flex w-screen h-screen gap-4 p-4">
  <!-- Sidebar -->
  <div class="bg-red-100 w-64 shrink-0 rounded-xl p-4">Postfach</div>

  <!-- Main area -->
  <div class="grid grid-cols-2 grid-rows-[auto_1fr] gap-4 flex-1 min-w-0">
    <div class="bg-green-100 col-span-2 rounded-xl p-4 flex items-center">Tools</div>
    <div class="bg-blue-100 rounded-xl p-4 min-h-0 overflow-auto"><EmailList /></div>
    <div class="bg-violet-100 rounded-xl p-4 min-h-0 overflow-auto">Content</div>
  </div>
</div>

<style lang="postcss">
  @reference "tailwindcss";
  :global(html) {
    background-color: theme(--color-gray-100);
  }
</style>
