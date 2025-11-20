using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace Sinout.Model
{
    public class AnalyzeRequest
    {
        public string ImageBase64 { get; set; }
        public string? Model { get; set; }
        public string? Detector { get; set; }
    }
}