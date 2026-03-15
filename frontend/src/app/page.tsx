/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable @next/next/no-img-element */
"use client"

import { useState, useRef } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { UploadCloud, Sparkles, Link as LinkIcon, Image as ImageIcon, Layers, CheckCircle2, Loader2 } from "lucide-react"
import axios from "axios"

import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"

const API_URL = "http://localhost:8000"

const SCENES_PRESET = [
  "🎯 产品主图 - 白底产品展示",
  "✨ 功效展示图 - 数据可视化",
  "🔬 成分说明图 - 科学配方",
  "🛁 使用场景图 - 生活场景",
  "📖 品牌故事图 - 品牌背景"
]

export default function Home() {
  const [activeTab, setActiveTab] = useState("analyze")
  const [styleImages, setStyleImages] = useState<File[]>([])
  const [analyzing, setAnalyzing] = useState(false)
  const [styleDesc, setStyleDesc] = useState("")
  const [repPaths, setRepPaths] = useState<string[]>([])
  const [repUrls, setRepUrls] = useState<string[]>([])

  const [userPrompt, setUserPrompt] = useState("")
  const [fusing, setFusing] = useState(false)
  const [fusedPrompt, setFusedPrompt] = useState("")

  const [productImage, setProductImage] = useState<File | null>(null)
  const [aspectRatio, setAspectRatio] = useState("3:4")
  
  const [generatingSingle, setGeneratingSingle] = useState(false)
  const [singleResults, setSingleResults] = useState<string[]>([])

  const [generatingBatch, setGeneratingBatch] = useState(false)
  const [selectedScenes, setSelectedScenes] = useState<number[]>([0, 1, 2, 3, 4])
  const [batchResults, setBatchResults] = useState<string[]>([])
  const [batchLogs, setBatchLogs] = useState<string[]>([])

  const fileInputRef = useRef<HTMLInputElement>(null)
  const productInputRef1 = useRef<HTMLInputElement>(null)
  const productInputRef2 = useRef<HTMLInputElement>(null)

  const handleStyleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setStyleImages(Array.from(e.target.files))
    }
  }

  const handleProductUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setProductImage(e.target.files[0])
    }
  }

  const analyzeStyle = async () => {
    if (styleImages.length === 0) return alert("Please upload style images")
    setAnalyzing(true)
    try {
      const formData = new FormData()
      styleImages.forEach(file => formData.append("images", file))
      
      const res = await axios.post(`${API_URL}/api/analyze`, formData)
      setStyleDesc(res.data.description)
      setRepPaths(res.data.representative_paths)
      setRepUrls(res.data.representative_urls)
    } catch (err: any) {
      alert(err.response?.data?.detail || "Analysis failed")
    } finally {
      setAnalyzing(false)
    }
  }

  const fusePrompt = async () => {
    if (!styleDesc) return alert("Please analyze style first")
    if (!userPrompt) return alert("Please enter user prompt")
    setFusing(true)
    try {
      const res = await axios.post(`${API_URL}/api/fuse`, {
        template_description: styleDesc,
        user_prompt: userPrompt
      })
      setFusedPrompt(res.data.fused_prompt)
    } catch (err: any) {
      alert("Fusion failed")
    } finally {
      setFusing(false)
    }
  }

  const generateSingle = async () => {
    if (!fusedPrompt) return alert("Please fuse prompt first")
    if (!productImage) return alert("Please upload product image")
    setGeneratingSingle(true)
    try {
      const formData = new FormData()
      formData.append("fused_prompt", fusedPrompt)
      formData.append("aspect_ratio", aspectRatio)
      formData.append("style_references", repPaths.join(","))
      formData.append("product_image", productImage)

      const res = await axios.post(`${API_URL}/api/generate/single`, formData)
      setSingleResults(res.data.result_urls)
    } catch (err: any) {
      alert("Generation failed")
    } finally {
      setGeneratingSingle(false)
    }
  }

  const generateBatch = async () => {
    if (!styleDesc) return alert("Please analyze style first")
    if (!productImage) return alert("Please upload product image")
    if (selectedScenes.length === 0) return alert("Please select at least one scene")
    
    setGeneratingBatch(true)
    setBatchLogs([])
    setBatchResults([])
    try {
      const formData = new FormData()
      formData.append("template_description", styleDesc)
      formData.append("aspect_ratio", aspectRatio)
      formData.append("style_references", repPaths.join(","))
      formData.append("scenes", selectedScenes.join(","))
      formData.append("product_image", productImage)

      const res = await axios.post(`${API_URL}/api/generate/batch`, formData)
      setBatchResults(res.data.generated_urls)
      setBatchLogs(res.data.logs)
    } catch (err: any) {
      alert("Batch generation failed")
    } finally {
      setGeneratingBatch(false)
    }
  }

  const toggleScene = (index: number) => {
    setSelectedScenes(prev => 
      prev.includes(index) ? prev.filter(i => i !== index) : [...prev, index]
    )
  }

  return (
    <div className="min-h-screen bg-black text-white bg-gradient-animated p-6 font-sans">
      <div className="max-w-5xl mx-auto space-y-8">
        <header className="text-center py-10 space-y-4">
          <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="inline-block p-3 rounded-2xl glass mb-4">
            <Sparkles className="w-8 h-8 text-purple-400" />
          </motion.div>
          <motion.h1 initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-4xl md:text-5xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-blue-400">
            Style Template V2
          </motion.h1>
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }} className="text-white/60 text-lg">
            Liquid Glass Interface • Dual Reference Architecture
          </motion.p>
        </header>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid grid-cols-4 w-full glass p-1 rounded-xl h-auto mb-8">
            <TabsTrigger value="analyze" className="rounded-lg py-3 data-[state=active]:bg-white/10 data-[state=active]:text-white transition-all text-white/50"><ImageIcon className="w-4 h-4 mr-2"/> Analyze</TabsTrigger>
            <TabsTrigger value="fuse" className="rounded-lg py-3 data-[state=active]:bg-white/10 data-[state=active]:text-white transition-all text-white/50"><LinkIcon className="w-4 h-4 mr-2"/> Fuse</TabsTrigger>
            <TabsTrigger value="single" className="rounded-lg py-3 data-[state=active]:bg-white/10 data-[state=active]:text-white transition-all text-white/50"><Sparkles className="w-4 h-4 mr-2"/> Generate</TabsTrigger>
            <TabsTrigger value="batch" className="rounded-lg py-3 data-[state=active]:bg-white/10 data-[state=active]:text-white transition-all text-white/50"><Layers className="w-4 h-4 mr-2"/> Batch</TabsTrigger>
          </TabsList>

          <AnimatePresence mode="wait">
            {activeTab === "analyze" && (
              <TabsContent value="analyze" key="analyze" forceMount>
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="glass-card p-8 space-y-6">
                  <div 
                    onClick={() => fileInputRef.current?.click()}
                    className="border-2 border-dashed border-white/20 rounded-xl p-10 text-center cursor-pointer hover:bg-white/5 hover:border-white/40 transition-all flex flex-col items-center justify-center space-y-4"
                  >
                    <UploadCloud className="w-10 h-10 text-white/40" />
                    <p className="text-white/60">Click or drag style images here to analyze</p>
                    <input type="file" multiple hidden ref={fileInputRef} onChange={handleStyleUpload} accept="image/*" />
                  </div>
                  {styleImages.length > 0 && (
                    <p className="text-sm text-purple-300 font-medium">{styleImages.length} images selected</p>
                  )}
                  
                  <Button onClick={analyzeStyle} disabled={analyzing} className="w-full bg-white/10 hover:bg-white/20 text-white border border-white/10 rounded-xl py-6 h-auto text-lg backdrop-blur-md">
                    {analyzing ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : <Sparkles className="w-5 h-5 mr-2" />}
                    {analyzing ? "Analyzing Template..." : "Analyze Style"}
                  </Button>

                  {styleDesc && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4 pt-6 border-t border-white/10">
                      <div>
                        <Label className="text-white/70 mb-2 block">Style Description</Label>
                        <Textarea value={styleDesc} readOnly className="glass-input min-h-[120px]" />
                      </div>
                      {repUrls.length > 0 && (
                        <div>
                          <Label className="text-white/70 mb-2 block">Representative Images</Label>
                          <div className="flex gap-4 overflow-x-auto pb-4">
                            {repUrls.map((url, i) => (
                              <img key={i} src={`${API_URL}${url}`} alt="Rep" className="h-32 rounded-lg border border-white/20 object-cover shadow-lg" />
                            ))}
                          </div>
                        </div>
                      )}
                    </motion.div>
                  )}
                </motion.div>
              </TabsContent>
            )}

            {activeTab === "fuse" && (
              <TabsContent value="fuse" key="fuse" forceMount>
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="glass-card p-8 space-y-6">
                  <div>
                    <Label className="text-white/70 mb-2 block">User Prompt (What to generate?)</Label>
                    <Textarea 
                      placeholder="e.g. A CeraVe cleanser product..." 
                      value={userPrompt} 
                      onChange={e => setUserPrompt(e.target.value)} 
                      className="glass-input" 
                    />
                  </div>
                  
                  <Button onClick={fusePrompt} disabled={fusing} className="w-full bg-white/10 hover:bg-white/20 text-white border border-white/10 rounded-xl py-6 h-auto text-lg backdrop-blur-md">
                    {fusing ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : <LinkIcon className="w-5 h-5 mr-2" />}
                    {fusing ? "Fusing Prompts..." : "Fuse Prompt"}
                  </Button>

                  {fusedPrompt && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="pt-6 border-t border-white/10">
                      <Label className="text-white/70 mb-2 block">Fused Prompt</Label>
                      <Textarea value={fusedPrompt} onChange={e => setFusedPrompt(e.target.value)} className="glass-input min-h-[120px]" />
                    </motion.div>
                  )}
                </motion.div>
              </TabsContent>
            )}

            {activeTab === "single" && (
              <TabsContent value="single" key="single" forceMount>
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="grid md:grid-cols-2 gap-8">
                  <div className="glass-card p-8 space-y-6">
                    <div>
                      <Label className="text-white/70 mb-2 block">Fused Prompt</Label>
                      <Textarea value={fusedPrompt} readOnly className="glass-input h-[100px]" placeholder="Go to Fuse tab first..." />
                    </div>
                    
                    <div>
                      <Label className="text-white/70 mb-2 block">Product Reference Image</Label>
                      <div 
                        onClick={() => productInputRef1.current?.click()}
                        className="border-2 border-dashed border-white/20 rounded-xl p-6 text-center cursor-pointer hover:bg-white/5 transition-all flex flex-col items-center"
                      >
                        <ImageIcon className="w-8 h-8 text-white/40 mb-2" />
                        <p className="text-white/60 text-sm">Upload Product Image</p>
                        <input type="file" hidden ref={productInputRef1} onChange={handleProductUpload} accept="image/*" />
                      </div>
                      {productImage && <p className="text-xs text-green-400 mt-2 flex items-center"><CheckCircle2 className="w-3 h-3 mr-1"/> {productImage.name}</p>}
                    </div>

                    <div>
                      <Label className="text-white/70 mb-2 block">Aspect Ratio</Label>
                      <select value={aspectRatio} onChange={e => setAspectRatio(e.target.value)} className="w-full rounded-lg glass-input p-3 outline-none appearance-none">
                        <option value="1:1">1:1 Square</option>
                        <option value="3:4">3:4 Portrait</option>
                        <option value="4:3">4:3 Landscape</option>
                        <option value="16:9">16:9 Widescreen</option>
                      </select>
                    </div>

                    <Button onClick={generateSingle} disabled={generatingSingle} className="w-full bg-gradient-to-r from-purple-600/50 to-blue-600/50 hover:from-purple-500/60 hover:to-blue-500/60 text-white border border-white/20 rounded-xl py-6 h-auto text-lg shadow-lg">
                      {generatingSingle ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : <Sparkles className="w-5 h-5 mr-2" />}
                      {generatingSingle ? "Generating..." : "Generate Image"}
                    </Button>
                  </div>

                  <div className="glass-card p-8 flex flex-col">
                    <Label className="text-white/70 mb-4 block">Generation Result</Label>
                    <div className="flex-1 rounded-xl bg-black/20 border border-white/5 flex items-center justify-center overflow-hidden relative">
                      {singleResults.length > 0 ? (
                        <div className="grid grid-cols-1 gap-4 w-full h-full p-4 overflow-y-auto">
                          {singleResults.map((url, i) => (
                            <img key={i} src={`${API_URL}${url}`} className="w-full rounded-lg object-contain shadow-2xl" alt="Result" />
                          ))}
                        </div>
                      ) : (
                        <p className="text-white/30 text-sm">Output will appear here</p>
                      )}
                    </div>
                  </div>
                </motion.div>
              </TabsContent>
            )}

            {activeTab === "batch" && (
              <TabsContent value="batch" key="batch" forceMount>
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="grid md:grid-cols-2 gap-8">
                  <div className="glass-card p-8 space-y-6">
                    <div>
                      <Label className="text-white/70 mb-2 block">Product Reference Image</Label>
                      <div 
                        onClick={() => productInputRef2.current?.click()}
                        className="border-2 border-dashed border-white/20 rounded-xl p-6 text-center cursor-pointer hover:bg-white/5 transition-all flex flex-col items-center"
                      >
                        <ImageIcon className="w-8 h-8 text-white/40 mb-2" />
                        <p className="text-white/60 text-sm">Upload Product Image</p>
                        <input type="file" hidden ref={productInputRef2} onChange={handleProductUpload} accept="image/*" />
                      </div>
                      {productImage && <p className="text-xs text-green-400 mt-2 flex items-center"><CheckCircle2 className="w-3 h-3 mr-1"/> {productImage.name}</p>}
                    </div>

                    <div>
                      <Label className="text-white/70 mb-3 block">Select Scenes</Label>
                      <div className="space-y-3">
                        {SCENES_PRESET.map((scene, i) => (
                          <div key={i} className="flex items-center space-x-3 p-3 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-colors">
                            <Checkbox id={`scene-${i}`} checked={selectedScenes.includes(i)} onCheckedChange={() => toggleScene(i)} className="border-white/40 data-[state=checked]:bg-purple-500 data-[state=checked]:border-purple-500" />
                            <Label htmlFor={`scene-${i}`} className="text-sm font-medium leading-none cursor-pointer flex-1">
                              {scene}
                            </Label>
                          </div>
                        ))}
                      </div>
                    </div>

                    <Button onClick={generateBatch} disabled={generatingBatch} className="w-full bg-gradient-to-r from-blue-600/50 to-indigo-600/50 hover:from-blue-500/60 hover:to-indigo-500/60 text-white border border-white/20 rounded-xl py-6 h-auto text-lg shadow-lg">
                      {generatingBatch ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : <Layers className="w-5 h-5 mr-2" />}
                      {generatingBatch ? "Processing Batch..." : "Batch Generate Setup"}
                    </Button>
                  </div>

                  <div className="glass-card p-8 flex flex-col space-y-4">
                    <div>
                      <Label className="text-white/70 mb-2 block">Batch Results</Label>
                      <div className="h-64 rounded-xl bg-black/20 border border-white/5 flex items-center justify-center overflow-y-auto p-4">
                        {batchResults.length > 0 ? (
                          <div className="grid grid-cols-2 gap-4">
                            {batchResults.map((url, i) => (
                              <img key={i} src={`${API_URL}${url}`} className="w-full rounded-lg object-cover shadow-xl" alt="Batch Result" />
                            ))}
                          </div>
                        ) : (
                          <p className="text-white/30 text-sm">Images will appear here</p>
                        )}
                      </div>
                    </div>

                    <div className="flex-1">
                      <Label className="text-white/70 mb-2 block">Execution Logs</Label>
                      <div className="h-full min-h-[100px] rounded-xl bg-black/40 border border-white/5 p-4 font-mono text-xs text-green-400 overflow-y-auto">
                        {batchLogs.length > 0 ? (
                          batchLogs.map((log, i) => <div key={i} className="mb-1 opacity-80">{log}</div>)
                        ) : (
                          <p className="text-white/20">Waiting to start...</p>
                        )}
                      </div>
                    </div>
                  </div>
                </motion.div>
              </TabsContent>
            )}
          </AnimatePresence>
        </Tabs>
      </div>
    </div>
  )
}