<script lang="ts">
  import type { MailDTO } from "../routes/api/mail/+server";
  import { cleanEmailBody, formatSender } from "./utils";


    let { mail }: { mail: MailDTO} = $props()

    console.log("mail Object:", mail)
    console.log("mail.body: ", typeof mail.body)
    console.log("mail.bodyHtml: ", typeof mail.bodyHtml)
    console.log("mail.bodyPlain: ", typeof mail.bodyPlain)


</script>


<li class="border-2 rounded-lg py-2 pl-2 pr-8 my-2">
    <a href=".">{formatSender(mail.sender)}</a>
    <h2 class="text-xl font-bold">{mail.subject}</h2>
    <p>{cleanEmailBody(mail.bodyHtml).slice(0, 200)}</p>
    <!-- <p>{formatBody(mail.body)}</p> -->
    <!-- <p>{mail.bodyHtml}</p> -->
    <!-- <p>{@html mail.bodyHtml}</p> -->
</li>