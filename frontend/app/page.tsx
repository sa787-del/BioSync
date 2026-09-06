import { SiteHeader } from "@/components/site/site-header"
import { Hero } from "@/components/site/hero"
import { TrustStrip } from "@/components/site/trust-strip"
import { Platform } from "@/components/site/platform"
import { Conditions } from "@/components/site/conditions"
import { Approach } from "@/components/site/approach"
import { Trust } from "@/components/site/trust"
import { CtaFooter } from "@/components/site/cta-footer"

export default function Page() {
  return <div className="min-h-screen bg-background"><SiteHeader /><main><Hero /><TrustStrip /><Platform /><Conditions /><Approach /><Trust /><CtaFooter /></main></div>
}
