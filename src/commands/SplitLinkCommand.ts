/*  SplitLinkCommand.ts  */
import {
  DefaultLinkModel,
  DiagramModel
} from '@projectstorm/react-diagrams';
import { Point } from '@projectstorm/geometry';
import { CustomPortModel } from '../components/port/CustomPortModel';

export class SplitLinkCommand {
  constructor(
    private diagramModel : DiagramModel,
    private draggedNode   : any,      
    private linkId        : string,    
    private dropPosition  : Point    
  ) {}

 
  private linkPreservingAllRules(src: CustomPortModel, dst: CustomPortModel): DefaultLinkModel | null {
    Object.values(src.getLinks()).forEach(l => this.diagramModel.removeLink(l));
    Object.values(dst.getLinks()).forEach(l => this.diagramModel.removeLink(l));

    if (!src.canLinkToPort(dst)) {
      console.warn('[SplitLink] no link CustomPortModel.canLinkToPort().');
      return null;
    }

    const newLink = src.link(dst);
    if (newLink) {
      this.diagramModel.addLink(newLink);
    }
    return null;
  }

  execute(): void {
    const oldLink = this.diagramModel.getLink(this.linkId) as DefaultLinkModel;
    if (!oldLink) return;

    const srcPort = oldLink.getSourcePort() as CustomPortModel;
    const dstPort = oldLink.getTargetPort() as CustomPortModel;
    if (!srcPort || !dstPort) return;

    if (!this.diagramModel.getNode(this.draggedNode.getID())) {
      this.diagramModel.addNode(this.draggedNode);
    }
    this.draggedNode.setPosition(this.dropPosition.x, this.dropPosition.y);

    const inPort  = this.draggedNode.getPort('in-0')  as CustomPortModel;
    const outPort = this.draggedNode.getPort('out-0') as CustomPortModel;
    if (!inPort || !outPort) {
      console.warn('[SplitLink]new nodes des not have in-0 أو out-0.');
      return;
    }

    this.diagramModel.removeLink(oldLink);

    Object.values(srcPort.getLinks()).forEach(l => this.diagramModel.removeLink(l));
    Object.values(inPort.getLinks()).forEach(l => this.diagramModel.removeLink(l));
    Object.values(dstPort.getLinks()).forEach(l => this.diagramModel.removeLink(l));

    this.linkPreservingAllRules(srcPort, inPort);

    this.linkPreservingAllRules(outPort, dstPort);
  }
}
