<script lang="ts">
  import { onMount } from "svelte";
  import type { MailDTO, MailDtoRes } from "../routes/api/mail/+server";

    let mails: MailDTO[] = $state([]);
    let loading = $state(true);
    let error = $state<string | null>(null);

    onMount(async () => {
        try {
            const res = await fetch(`/api/mail?page=1&batchSize=5`)
            if (!res.ok) throw new Error("Failed to fetch mails")

            const data = await res.json() as MailDtoRes
            mails = data.mails
        } catch(err: any) {
            error = err.message
        } finally {
            loading = false
        }
    })

</script>

{#if loading}
    <p>Loading...</p>
{:else if error}
    <p style="color:red;">{error}</p>
{:else}
    <ul>
        {#each mails as mail}
            <li>
                <strong>{mail.subject}</strong><br />
                <small>{mail.sender} - {mail.date}</small>
                <!-- <p>{mail.body}</p> -->
            </li>
        {/each}
    </ul>
{/if}